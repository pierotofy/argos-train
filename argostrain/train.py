#!/usr/bin/env python3

import json
import shutil
import os
import subprocess
import sys
from pathlib import Path

import stanza

import argostrain
import argostrain.opennmtutils
from argostrain import data, settings
from argostrain.dataset import *
from argostrain.sources import get_network_dataset

def train(
    source,
    version,
    package_version,
    argos_version,
):
    from_code = source['from_code']
    to_code = source['to_code']
    from_name = source['from_name']
    to_name = source['to_name']
    data = source['data']


    settings.RUN_PATH.mkdir(exist_ok=True)
    settings.CACHE_PATH.mkdir(exist_ok=True)

    # Delete training data if it exists
    if settings.SOURCE_PATH.exists() or settings.TARGET_PATH.exists():
        print("Data already exists and will be deleted")
        settings.SOURCE_PATH.unlink(missing_ok=True)
        settings.TARGET_PATH.unlink(missing_ok=True)

        
    assert len(data) > 0

    # Download and write data source and target
    while len(data) > 0:
        dataset = get_network_dataset(source, data.pop())
        print(str(dataset))
        src, tgt = dataset.data()

        with open(settings.SOURCE_PATH, "a") as s:
            s.writelines(src)

        with open(settings.TARGET_PATH, "a") as t:
            t.writelines(tgt)

        del dataset

    # Generate README.md
    readme = f"# {from_name}-{to_name}"
    with open(settings.RUN_PATH / "README.md", "w") as readme_file:
        readme_file.write(readme)

    # Generate metadata.json
    metadata = {
        "package_version": package_version,
        "argos_version": argos_version,
        "from_code": from_code,
        "from_name": from_name,
        "to_code": to_code,
        "to_name": to_name,
    }
    metadata_json = json.dumps(metadata, indent=4)
    with open(settings.RUN_PATH / "metadata.json", "w") as metadata_file:
        metadata_file.write(metadata_json)

    argostrain.data.prepare_data(settings.SOURCE_PATH, settings.TARGET_PATH)

    with open(Path("run/split_data/all.txt"), "w") as combined:
        with open(Path("run/split_data/src-train.txt")) as src:
            for line in src:
                combined.write(line)
        with open(Path("run/split_data/tgt-train.txt")) as tgt:
            for line in tgt:
                combined.write(line)

    # TODO: Don't hardcode vocab_size and set user_defined_symbols
    subprocess.run(
        [
            "spm_train",
            "--input=run/split_data/all.txt",
            "--model_prefix=run/sentencepiece",
            "--vocab_size=50000",
            "--character_coverage=1.0", # for small character set, 0.9995 for Japanese/Chinese
            "--input_sentence_size=1000000",
            "--shuffle_input_sentence=true",
        ]
    )

    subprocess.run(["rm", "run/split_data/all.txt"])

    if os.path.exists("run/opennmt_data"):
        shutil.rmtree("run/opennmt_data")

    subprocess.run(["onmt_build_vocab", "-config", "config.yml", "-n_sample", "-1"])

    subprocess.run(["onmt_train", "-config", "config.yml"])

    # Average checkpoints
    opennmt_checkpoints = argostrain.opennmtutils.get_checkpoints()
    opennmt_checkpoints.sort()
    subprocess.run(
        [
            "./../OpenNMT-py/tools/average_models.py",
            "-m",
            str(opennmt_checkpoints[-2].f),
            str(opennmt_checkpoints[-1].f),
            "-o",
            "run/averaged.pt",
        ]
    )

    subprocess.run(
        [
            "ct2-opennmt-py-converter",
            "--model_path",
            "run/averaged.pt",
            "--output_dir",
            "run/model",
            "--quantization",
            "int8",
        ]
    )

    package_version_code = package_version.replace(".", "_")
    model_dir = f"translate-{from_code}_{to_code}-{package_version_code}"
    model_path = Path("run") / model_dir

    subprocess.run(["mkdir", model_path])

    subprocess.run(["cp", "-r", "run/model", model_path])

    subprocess.run(["cp", "run/sentencepiece.model", model_path])

    # Include a Stanza sentence boundary detection model
    stanza_model_located = False
    stanza_lang_code = from_code
    while not stanza_model_located:
        try:
            stanza.download(stanza_lang_code, dir="run/stanza", processors="tokenize")
            stanza_model_located = True
        except:
            print(f"Could not locate stanza model for lang {stanza_lang_code}")
            print(
                "Enter the code of a different language to attempt to use its stanza model."
            )
            print(
                "This will work best for with a similar language to the one you are attempting to translate."
            )
            print(
                "This will require manually editing the Stanza package in the finished model to change its code"
            )
            stanza_lang_code = input("Stanza language code (ISO 639): ")

    subprocess.run(["cp", "-r", "run/stanza", model_path])

    subprocess.run(["cp", "run/metadata.json", model_path])
    subprocess.run(["cp", "run/README.md", model_path])

    package_path = (
        Path("run")
        / f"translate-{from_code}_{to_code}-{package_version_code}.argosmodel"
    )

    shutil.make_archive(model_dir, "zip", root_dir="run", base_dir=model_dir)
    subprocess.run(["mv", model_dir + ".zip", package_path])

    print(f"Package saved to {str(package_path.resolve())}")
