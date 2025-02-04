# Contributing Code & Datasets

## Installing and running tests

First, check out the repository from Github. (That's `git clone git@github.com:mir-dataset-loaders/mirdata.git`)

Then, install [pyenv](https://github.com/pyenv/pyenv#installation) to manage your Python versions.
You'll want to install Python 2.7.11, and the latest versions of Python 3.6 and 3.7

Once pyenv and the three versions of Python are installed, install [tox](https://tox.readthedocs.io/en/latest/), our test runner.

Finally, run tox with `tox`.  All tests should pass!


## Contributing a new dataset loader

To add a new dataset loader:

1. Create a script in `scripts/`, e.g. `make_my_dataset_index.py`, which generates an index file. (See below for what an index file is!)
2. Run the script on the canonical version of the dataset and save the index in `mirdata/indexes/` e.g. `my_dataset_index.json`. (Also see below for what we mean by "canonical"!)
3. Create a module in mirdata, e.g. `mirdata/my_dataset.py`
4. Create tests for your loader in `tests/`, e.g. `test_my_dataset.py`
5. Add your module to `docs/source/mirdata.rst`
6. Add the module to `mirdata/__init__.py`

### Canonical datasets
Whenever possible, this should be the official release of the dataset as published by the dataset creator/s.
When this is not possible, (e.g. for data that is no longer available), find as many copies of the data as you can from different researchers (at least 4), and use the most common one. When in doubt open an [issue](https://github.com/mir-dataset-loaders/mirdata/issues) and leave it to the community to discuss what to use.

### Creating an index

The index should be a json file where the top level keys are the unique track
ids of the dataset. The values should be a dictionary of files associated with
the track id, along with their checksums.

Any file path included should be relative to the top level directory of the dataset.
For example, if a dataset has the structure:
```
> Example_Dataset/
    > audio/
        track1.wav
        track2.wav
        track3.wav
    > annotations/
        track1.csv
        Track2.csv
        track3.csv
```
The top level directory is `Example_Dataset` and the relative path for `track1.wav`
should be `audio/track1.wav`.

Any unavailable field should be indicated with `null`.

A possible index file for this example would be:
```javascript
{
    "track1": {
        "audio": [
            "audio/track1.wav",  // the relative path for track1's audio file
            "912ec803b2ce49e4a541068d495ab570"  // track1.wav's md5 checksum
        ],
        "annotation": [
            "annotations/track1.csv",  // the relative path for track1's annotation
            "2cf33591c3b28b382668952e236cccd5"  // track1.csv's md5 checksum
        ]
    },
    "track2": {
        "audio": [
            "audio/track2.wav",
            "65d671ec9787b32cfb7e33188be32ff7"
        ],
        "annotation": [
            "annotations/Track2.csv",
            "e1964798cfe86e914af895f8d0291812"
        ]
    },
    "track3": {
        "audio": [
            "audio/track3.wav",
            "60edeb51dc4041c47c031c4bfb456b76"
        ],
        "annotation": [
            "annotations/track3.csv",
            "06cb006cc7b61de6be6361ff904654b3"
        ]
  }
}
```

In this example there is a (purposeful) mismatch between the name of the audio file `track2.wav` and its corresponding annotation file, `Track2.csv`, compared with the other pairs. *This mismatch should be included in the index*. This type of slight difference in filenames happens often in publicly available datasets, making pairing audio and annotation files more difficult. We use a fixed, version-controlled index to account for this kind of mismatch, rather than relying on string parsing on load.

Scripts used to create the dataset indexes are in the [scripts](https://github.com/mir-dataset-loaders/mirdata/tree/master/scripts) folder. For a standard example, see the [script used to make the Example indexhttps://github.com/mir-dataset-loaders/mirdata/blob/master/scripts/make_ikala_index.py](https://github.com/mir-dataset-loaders/mirdata/blob/master/scripts/make_ikala_index.py).


### Creating a module.

Copy and paste this template and adjust it for your dataset. Find and replace `Example` with the name of your dataset.
You can also remove any comments beginning with `# --`

```python

# -*- coding: utf-8 -*-
"""Example Dataset Loader

[Description of the dataset]

[Link to any relevant websites]

Attributes:
    DATASET_DIR (str): The directory name for Example dataset. Set to `'Example'`.

    INDEX (dict): {track_id: track_data}.
        track_data is a `Track` namedtuple.

    METADATA (dict): Dictionary of track metadata
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# -- import whatever you need here

import mirdata.utils as utils
import mirdata.download_utils as download_utils

DATASET_DIR = 'Example'
INDEX = utils.load_json_index('example_index.json')
METADATA = None  # -- This is set to None initially and loaded when accessed
# -- info for any files that need to be downloaded
REMOTE_ZIP = download_utils.RemoteFileMetadata(
    filename='a_zip_file.zip',
    url='http://website/hosting/the/zipfile.zip',
    checksum='00000000000000000000000000000000',  # -- the md5 checksum
    destination_dir='path/to/unzip' # -- relative path for where to unzip the data, or None
)


class Track(object):
    """Example track class

    Args:
        track_id (str): track id of the track
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets/Example`

    Attributes:
        track_id (str): track id
        # -- Add any of the dataset specific attributes here

    """
    def __init__(self, track_id, data_home=None):
        if track_id not in INDEX:
            raise ValueError(
                '{} is not a valid track ID in Example'.format(track_id))

        # -- Not necessary for all datasets, but if yours has metadata,
        # -- load it like this
        if METADATA is None or METADATA['data_home'] != data_home:
            _reload_metadata(data_home)

        self.track_id = track_id

        if data_home is None:
            data_home = utils.get_default_dataset_path(DATASET_DIR)

        self._data_home = data_home
        self._track_paths = INDEX[track_id]

        # -- add any dataset specific attributes here
        self.audio_path = os.path.join(
            self._data_home, self._track_paths['audio'][0])

        # -- if the user doesn't have a metadata file, load None
        if METADATA is not None and track_id in METADATA:
            self.some_metadata = METADATA[track_id]['some_metadata']
        else:
            self.some_metadata = None

    # -- this lets users run `print(Track)` and get actual information
    def __repr__(self):
        repr_string = "Example Track(track_id={}, audio_path={}, " + \
            "some_metadata{}, "
            "annotation=AnnotationData('start_times', 'end_times', 'annotation'), " + \
        return repr_string.format(
            self.track_id, self.audio_path, self.some_metadata)

    # -- `annotation` will behave like an attribute, but it will only be loaded
    # -- and saved when someone accesses it. Useful when loading slightly
    # -- bigger files or for bigger datasets. By default, we make any time
    # -- series data loaded from a file a cached property
    @utils.cached_property
    def annotation(self):
        return _load_annotation(os.path.join(
            self._data_home, self._track_paths['annotation'][0]))

    # -- `audio` will behave like an attribute, but it will only be loaded
    # -- when someone accesses it and it won't be stored. By default, we make
    # -- any memory heavy information (like audio) properties
    @property
    def audio(self):
        """Load audio.

        Returns:
            audio (np.array): audio. size of `(N, )`
            sr (int): sampling rate of the audio file
        """
        # -- By default we load to mono
        # -- change this if it doesn't make sense for your dataset.
        audio, sr = librosa.load(self.audio_path, sr=None, mono=True)
        return audio, sr


def download(data_home=None, force_overwrite=False):
    """Download the dataset.

    Args:
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets`
        force_overwrite (bool): If True, existing files are overwritten by the
            downloaded files.
    """
    if data_home is None:
        data_home = utils.get_default_dataset_path(DATASET_DIR)

    download_utils.downloader(
        # -- everything will be downloaded & uncompressed inside `data_home`
        data_home,
        force_overwrite=force_overwrite,
        # -- download any freely accessible zip files by adding them to this list
        # -- this function also unzips them
        zip_downloads=[REMOTE_ZIP],
        # -- download any freely accessible tar files by adding them to this list
        # -- this function also untarrs them
        tar_downloads=[...],
        # -- download any freely accessible uncompressed files by adding them to this list
        files_downloads=[...],
        # -- if you need to give the user any instructions, such as how to download
        # -- a dataset which is not freely availalbe, put them here
        print_message=""
    )

    # -- if the files need to be organized in a particular way, you can call
    # -- download_utils.downloader multiple times and change `data_home` to be
    # -- e.g. a subfolder of data_home.


# -- keep this function exactly as it is
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


# -- keep this function exactly as it is
def track_ids():
    """Return track ids
    Returns:
        (list): A list of track ids
    """
    return list(INDEX.keys())


# -- keep this function as it is
def load(data_home=None, silence_validator=False):
    """Load Example dataset
    Args:
        data_home (str): Local path where the dataset is stored.
            If `None`, looks for the data in the default directory, `~/mir_datasets`
    Returns:
        (dict): {`track_id`: track data}
    """
    if data_home is None:
        data_home = utils.get_default_dataset_path(DATASET_DIR)

    validate(data_home, silence=silence_validator)
    data = {}
    for key in INDEX.keys():
        data[key] = Track(key, data_home=data_home)
    return data


# -- Write any necessary loader functions for loading the dataset's data
def _load_annotation(annotation_path):
    if not os.path.exists(annotation_path):
        return None
    with open(annotation_path, 'r') as fhandle:
        reader = csv.reader(fhandle, delimiter=' ')
        start_times = []
        end_times = []
        annotation = []
        for line in reader:
            start_times.append(float(line[0]))
            end_times.append(float(line[1]))
            annotation.append(line[2])

    annotation_data = utils.EventData(
        np.array(start_times), np.array(end_times),
        np.array(annotation))
    return annotation_data


# -- keep this function as it is if you have metadata
def _reload_metadata(data_home):
    global METADATA
    METADATA = _load_metadata(data_home=data_home)


# -- change this to load any top-level metadata
def _load_metadata(data_home):
    if data_home is None:
        data_home = utils.get_default_dataset_path(DATASET_DIR)

    # load metadata however makes sense for your dataset
    metadata_path = os.path.join(data_home, 'example_metadata.json')
    with open(metadata_path, 'r') as fhandle:
        metadata = json.load(fhandle)

    metadata['data_home'] = data_home

    return metadata


def cite():
    """Print the reference"""

    cite_data = """
=========== MLA ===========
MLA format citation/s here
========== Bibtex ==========
Bibtex format citations/s here
"""
    print(cite_data)

```


## Adding tests to your dataset

1. Make a fake version of the dataset in the tests folder `tests/resources/mir_datasets/my_dataset/`, so you can test against that data. For example:
  a. Include all audio and annotation files for one track of the dataset
  b. For each audio/annotation file, reduce the audio length to a few seconds and remove all but a few of the annotations.
  c. If the dataset has a metadata file, reduce the length to a few lines to make it trival to test.
2. Test all of the dataset specific code, e.g. the Track object, any of the load functions, and so forth – see the ikala dataset tests (`tests/test_ikala.py`) for reference.
