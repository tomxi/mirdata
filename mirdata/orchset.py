# -*- coding: utf-8 -*-
"""ORCHSET Dataset Loader

Orchset is intended to be used as a dataset for the development and
evaluation of melody extraction algorithms. This collection contains
64 audio excerpts focused on symphonic music with their corresponding
annotation of the melody.

Details can be found at https://zenodo.org/record/1289786#.XREpzaeZPx6


Attributes:
    INDEX (dict): {track_id: track_data}.
        track_data is a jason data loaded from `index/`

    DIR (str): The directory name for ORCHSET.
        Set to `'Orchset'`.

    METADATA

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import csv
import glob
import librosa
import logging
import numpy as np
import os
import shutil

import mirdata.utils as utils
import mirdata.download_utils as download_utils

INDEX = utils.load_json_index('orchset_index.json')

REMOTE = download_utils.RemoteFileMetadata(
    filename='Orchset_dataset_0.zip',
    url='https://zenodo.org/record/1289786/files/Orchset_dataset_0.zip?download=1',
    checksum='cf6fe52d64624f61ee116c752fb318ca',
    destination_dir=None,
)

DATASET_DIR = 'Orchset'
METADATA = None


class Track(object):
    """ORCHSET Track class

    Args:
        track_id (str): track id of the Track
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets`

    Attributes:
        track_id (str): track id
        audio_path_mono (str): mono audio path of the track
        audio_path_stereo (str): stereo audio path of the track
        composer (str): composer
        work (str):
        predominant_melodic_instruments (str):
        alternating_melody
        contains_winds (bool?)
        contains_strings
        contains_brass
        only_strings
        only_winds
        only_brass
        melody (F0Data): melody annotation

    """

    def __init__(self, track_id, data_home=None):
        if track_id not in INDEX:
            raise ValueError('{} is not a valid track ID in Orchset'.format(track_id))

        self.track_id = track_id

        if data_home is None:
            data_home = utils.get_default_dataset_path(DATASET_DIR)

        self._data_home = data_home
        self._track_paths = INDEX[track_id]

        if METADATA is None or METADATA['data_home'] != data_home:
            _reload_metadata(data_home)

        if METADATA is not None and track_id in METADATA:
            self._track_metadata = METADATA[track_id]
        else:
            self._track_metadata = {
                'predominant_melodic_instruments-raw': None,
                'predominant_melodic_instruments-normalized': None,
                'alternating_melody': None,
                'contains_winds': None,
                'contains_strings': None,
                'contains_brass': None,
                'only_strings': None,
                'only_winds': None,
                'only_brass': None,
                'composer': None,
                'work': None,
                'excerpt': None,
            }

        self.audio_path_mono = os.path.join(
            self._data_home, self._track_paths['audio_mono'][0]
        )
        self.audio_path_stereo = os.path.join(
            self._data_home, self._track_paths['audio_stereo'][0]
        )
        self.composer = self._track_metadata['composer']
        self.work = self._track_metadata['work']
        self.excerpt = self._track_metadata['excerpt']
        self.predominant_melodic_instruments = self._track_metadata[
            'predominant_melodic_instruments-normalized'
        ]
        self.alternating_melody = self._track_metadata['alternating_melody']
        self.contains_winds = self._track_metadata['contains_winds']
        self.contains_strings = self._track_metadata['contains_strings']
        self.contains_brass = self._track_metadata['contains_brass']
        self.only_strings = self._track_metadata['only_strings']
        self.only_winds = self._track_metadata['only_winds']
        self.only_brass = self._track_metadata['only_brass']

    def __repr__(self):
        repr_string = (
            "Orchset Track(track_id={}, audio_path_stereo={}, "
            + "audio_path_mono={}, composer={}, work={}, excerpt={}, "
            + "predominant_melodic_instruments={}, alternating_melody={}, "
            + "contains_winds={}, contains_strings={}, contains_brass={}, "
            + "only_strings={}, only_winds={}, only_brass={}, "
            + "melody=F0Data('times', 'frequencies', 'confidence'))"
        )
        return repr_string.format(
            self.track_id,
            self.audio_path_stereo,
            self.audio_path_mono,
            self.composer,
            self.work,
            self.excerpt,
            self.predominant_melodic_instruments,
            self.alternating_melody,
            self.contains_winds,
            self.contains_strings,
            self.contains_brass,
            self.only_strings,
            self.only_winds,
            self.only_brass,
        )

    @utils.cached_property
    def melody(self):
        return _load_melody(
            os.path.join(self._data_home, self._track_paths['melody'][0])
        )

    @property
    def audio_mono(self):
        return librosa.load(self.audio_path_mono, sr=None)

    @property
    def audio_stereo(self):
        return librosa.load(self.audio_path_stereo, sr=None, mono=False)


def download(data_home=None, force_overwrite=False):
    """Download ORCHSET Dataset.

    Args:
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets`
        force_overwrite (bool): whether to overwrite the existing downloaded data

    """
    if data_home is None:
        data_home = utils.get_default_dataset_path(DATASET_DIR)

    download_utils.downloader(
        data_home, zip_downloads=[REMOTE], force_overwrite=force_overwrite
    )

    # files get downloaded to a folder called Orchset - move everything up a level
    duplicated_orchset_dir = os.path.join(data_home, 'Orchset')
    orchset_files = glob.glob(os.path.join(duplicated_orchset_dir, '*'))
    for fpath in orchset_files:
        shutil.move(fpath, data_home)
    os.removedirs(duplicated_orchset_dir)


def validate(data_home=None, silence=False):
    """Validate if the stored dataset is a valid version

    Args:
        dataset_path (str): ORCHSET dataset local path
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets`

    Returns:
        missing_files (list): List of file paths that are in the dataset index
            but missing locally
        invalid_checksums (list): List of file paths that file exists in the dataset
            index but has a different checksum compare to the reference checksum

    """

    missing_files, invalid_checksums = utils.validator(
        INDEX, data_home, silence=silence
    )
    return missing_files, invalid_checksums


def track_ids():
    """Return track ids

    Returns:
        (list): A list of track ids
    """
    return list(INDEX.keys())


def load(data_home=None, silence_validator=False):
    """Load ORCHSET dataset

    Args:
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets`

    Returns:
        (dict): {`track_id`: track data}

    """

    if data_home is None:
        data_home = utils.get_default_dataset_path(DATASET_DIR)

    validate(data_home, silence=silence_validator)
    orchset_data = {}
    for key in track_ids():
        orchset_data[key] = Track(key, data_home=data_home)
    return orchset_data


def _load_melody(melody_path):
    if not os.path.exists(melody_path):
        return None

    times = []
    freqs = []
    confidence = []
    with open(melody_path, 'r') as fhandle:
        reader = csv.reader(fhandle, delimiter='\t')
        for line in reader:
            times.append(float(line[0]))
            freqs.append(float(line[1]))
            confidence.append(0.0 if line[1] == '0' else 1.0)

    melody_data = utils.F0Data(np.array(times), np.array(freqs), np.array(confidence))
    return melody_data


def _load_metadata(data_home):

    predominant_inst_path = os.path.join(
        data_home, 'Orchset - Predominant Melodic Instruments.csv'
    )

    if not os.path.exists(predominant_inst_path):
        logging.info('Metadata file {} not found.'.format(predominant_inst_path))
        return None

    with open(predominant_inst_path, 'r') as fhandle:
        reader = csv.reader(fhandle, delimiter=',')
        raw_data = []
        for line in reader:
            if line[0] == 'excerpt':
                continue
            raw_data.append(line)

    tf_dict = {'TRUE': True, 'FALSE': False}

    metadata_index = {}
    for line in raw_data:
        track_id = line[0].split('.')[0]

        id_split = track_id.split('.')[0].split('-')
        if id_split[0] == 'Musorgski' or id_split[0] == 'Rimski':
            id_split[0] = '-'.join(id_split[:2])
            id_split.pop(1)

        melodic_instruments = [s.split(',') for s in line[1].split('+')]
        melodic_instruments = [
            item.lower() for sublist in melodic_instruments for item in sublist
        ]
        for i, inst in enumerate(melodic_instruments):
            if inst == 'string':
                melodic_instruments[i] = 'strings'
            elif inst == 'winds (solo)':
                melodic_instruments[i] = 'winds'
        melodic_instruments = sorted(list(set(melodic_instruments)))

        metadata_index[track_id] = {
            'predominant_melodic_instruments-raw': line[1],
            'predominant_melodic_instruments-normalized': melodic_instruments,
            'alternating_melody': tf_dict[line[2]],
            'contains_winds': tf_dict[line[3]],
            'contains_strings': tf_dict[line[4]],
            'contains_brass': tf_dict[line[5]],
            'only_strings': tf_dict[line[6]],
            'only_winds': tf_dict[line[7]],
            'only_brass': tf_dict[line[8]],
            'composer': id_split[0],
            'work': '-'.join(id_split[1:-1]),
            'excerpt': id_split[-1][2:],
        }

    metadata_index['data_home'] = data_home

    return metadata_index


def _reload_metadata(data_home):
    global METADATA
    METADATA = _load_metadata(data_home=data_home)


def cite():
    """Print the reference"""

    cite_data = """
===========  MLA ===========
Bosch, J., Marxer, R., Gomez, E., "Evaluation and Combination of
Pitch Estimation Methods for Melody Extraction in Symphonic
Classical Music", Journal of New Music Research (2016)

========== Bibtex ==========
@article{bosch2016evaluation,
    title={Evaluation and combination of pitch estimation methods for melody extraction in symphonic classical music},
    author={Bosch, Juan J and Marxer, Ricard and G{\'o}mez, Emilia},
    journal={Journal of New Music Research},
    volume={45},
    number={2},
    pages={101--117},
    year={2016},
    publisher={Taylor \\& Francis}
"""

    print(cite_data)
