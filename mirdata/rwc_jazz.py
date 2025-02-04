# -*- coding: utf-8 -*-
"""RWC Jazz Dataset Loader
"""
import csv
import librosa
import logging
import os

import mirdata.utils as utils
import mirdata.download_utils as download_utils

# these functions are identical for all rwc datasets
from mirdata.rwc_classical import _load_beats, _load_sections

INDEX = utils.load_json_index('rwc_jazz_index.json')
METADATA = None
METADATA_REMOTE = download_utils.RemoteFileMetadata(
    filename='rwc-j.csv',
    url='https://github.com/magdalenafuentes/metadata/archive/master.zip',
    checksum='7dbe87fedbaaa1f348625a2af1d78030',
    destination_dir=None,
)
DATASET_DIR = 'RWC-Jazz'
ANNOTATIONS_REMOTE_1 = download_utils.RemoteFileMetadata(
    filename='AIST.RWC-MDB-J-2001.BEAT.zip',
    url='https://staff.aist.go.jp/m.goto/RWC-MDB/AIST-Annotation/AIST.RWC-MDB-J-2001.BEAT.zip',
    checksum='b483853da05d0fff3992879f7729bcb4',
    destination_dir='annotations',
)
ANNOTATIONS_REMOTE_2 = download_utils.RemoteFileMetadata(
    filename='AIST.RWC-MDB-J-2001.CHORUS.zip',
    url='https://staff.aist.go.jp/m.goto/RWC-MDB/AIST-Annotation/AIST.RWC-MDB-J-2001.CHORUS.zip',
    checksum='44afcf7f193d7e48a7d99e7a6f3ed39d',
    destination_dir='annotations',
)


class Track(object):
    def __init__(self, track_id, data_home=None):
        if track_id not in INDEX:
            raise ValueError('{} is not a valid track ID in RWC-Jazz'.format(track_id))

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
                'piece_number': None,
                'suffix': None,
                'track_number': None,
                'title': None,
                'artist': None,
                'duration_sec': None,
                'variation': None,
                'instruments': None,
            }

        self.audio_path = os.path.join(self._data_home, self._track_paths['audio'][0])

        self.piece_number = self._track_metadata['piece_number']
        self.suffix = self._track_metadata['suffix']
        self.track_number = self._track_metadata['track_number']
        self.title = self._track_metadata['title']
        self.artist = self._track_metadata['artist']
        self.duration_sec = self._track_metadata['duration_sec']
        self.variation = self._track_metadata['variation']
        self.instruments = self._track_metadata['instruments']

    def __repr__(self):
        repr_string = (
            "RWC-Jazz Track(track_id={}, audio_path={}, "
            + "piece_number={}, suffix={}, track_number={}, title={}, "
            + "artist={}, duration_sec={}, variation={}, instruments={}, "
            + "sections=SectionData('start_times', 'end_times', 'sections'), "
            + "beats=BeatData('beat_times', 'beat_positions'))"
        )
        return repr_string.format(
            self.track_id,
            self.audio_path,
            self.piece_number,
            self.suffix,
            self.track_number,
            self.title,
            self.artist,
            self.duration_sec,
            self.variation,
            self.instruments,
        )

    @utils.cached_property
    def sections(self):
        return _load_sections(
            os.path.join(self._data_home, self._track_paths['sections'][0])
        )

    @utils.cached_property
    def beats(self):
        return _load_beats(os.path.join(self._data_home, self._track_paths['beats'][0]))

    @property
    def audio(self):
        return librosa.load(self.audio_path, sr=None, mono=True)


def download(data_home=None, force_overwrite=False):

    if data_home is None:
        data_home = utils.get_default_dataset_path(DATASET_DIR)

    info_message = """
        Unfortunately the audio files of the RWC-Jazz dataset are not available
        for download. If you have the RWC-Jazz dataset, place the contents into a
        folder called RWC-Jazz with the following structure:
            > RWC-Jazz/
                > annotations/
                > audio/rwc-j-m0i with i in [1 .. 4]
                > metadata-master/
        and copy the RWC-Jazz folder to {}
    """.format(
        data_home
    )

    download_utils.downloader(
        data_home,
        zip_downloads=[METADATA_REMOTE, ANNOTATIONS_REMOTE_1, ANNOTATIONS_REMOTE_2],
        info_message=info_message,
        force_overwrite=force_overwrite,
    )


def validate(data_home=None, silence=False):
    """Validate if the stored dataset is a valid version

    Args:
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets`

    Returns:
        missing_files (list): List of file paths that are in the dataset index
            but missing locally
        invalid_checksums (list): List of file paths that file exists in the dataset
            index but has a different checksum compare to the reference checksum

    """
    if data_home is None:
        data_home = utils.get_default_dataset_path(DATASET_DIR)

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
    """Load RWC-Jazz dataset

    Args:
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets`

    Returns:
        (dict): {`track_id`: track data}

    """
    if data_home is None:
        data_home = utils.get_default_dataset_path(DATASET_DIR)

    validate(data_home, silence=silence_validator)
    rwc_jazz_data = {}
    for key in track_ids():
        rwc_jazz_data[key] = Track(key, data_home=data_home)
    return rwc_jazz_data


def _load_metadata(data_home):

    metadata_path = os.path.join(data_home, 'metadata-master', 'rwc-j.csv')

    if not os.path.exists(metadata_path):
        logging.info(
            'Metadata file {} not found.'.format(metadata_path)
            + 'You can download the metadata file by running download()'
        )
        return None

    with open(metadata_path, 'r') as fhandle:
        dialect = csv.Sniffer().sniff(fhandle.read(1024))
        fhandle.seek(0)
        reader = csv.reader(fhandle, dialect)
        raw_data = []
        for line in reader:
            if line[0] != 'Piece No.':
                raw_data.append(line)

    metadata_index = {}
    for line in raw_data:
        if line[0] == 'Piece No.':
            continue
        p = '00' + line[0].split('.')[1][1:]
        track_id = 'RM-J{}'.format(p[len(p) - 3 :])

        metadata_index[track_id] = {
            'piece_number': line[0],
            'suffix': line[1],
            'track_number': line[2],
            'title': line[3],
            'artist': line[4],
            'duration_sec': line[5],
            'variation': line[6],
            'instruments': line[7],
        }

    metadata_index['data_home'] = data_home

    return metadata_index


def _reload_metadata(data_home):
    global METADATA
    METADATA = _load_metadata(data_home=data_home)


def cite():
    cite_data = """
===========  MLA ===========

Goto, Masataka, et al.,
"RWC Music Database: Popular, Classical and Jazz Music Databases.",
3rd International Society for Music Information Retrieval Conference (2002)

========== Bibtex ==========

@inproceedings{goto2002rwc,
  title={RWC Music Database: Popular, Classical and Jazz Music Databases.},
  author={Goto, Masataka and Hashiguchi, Hiroki and Nishimura, Takuichi and Oka, Ryuichi},
  booktitle={3rd International Society for Music Information Retrieval Conference},
  year={2002},
  series={ISMIR},
}

"""

    print(cite_data)
