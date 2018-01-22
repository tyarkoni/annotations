from os.path import join
from ..utils import get_test_data_path, DummyExtractor
from pliers.extractors import (LengthExtractor,
                               BrightnessExtractor,
                               SharpnessExtractor,
                               VibranceExtractor)
from pliers.stimuli import (ComplexTextStim, ImageStim, VideoStim,
                            AudioStim)
from pliers.support.download import download_nltk_data
from pliers.extractors.base import ExtractorResult, merge_results
import numpy as np
import pytest

TEXT_DIR = join(get_test_data_path(), 'text')


@pytest.fixture(scope='module')
def get_nltk():
    download_nltk_data()


def test_check_target_type():
    stim = ComplexTextStim(join(TEXT_DIR, 'sample_text.txt'),
                           columns='to', default_duration=1)
    td = SharpnessExtractor()
    with pytest.raises(TypeError):
        td.transform(stim)


def test_implicit_stim_iteration():
    np.random.seed(100)
    image_dir = join(get_test_data_path(), 'image')
    stim1 = ImageStim(join(image_dir, 'apple.jpg'))
    stim2 = ImageStim(join(image_dir, 'obama.jpg'))
    de = DummyExtractor()
    results = de.transform([stim1, stim2])
    assert len(results) == 2
    assert isinstance(results[0], ExtractorResult)


def test_implicit_stim_conversion():
    image_dir = join(get_test_data_path(), 'image')
    stim = ImageStim(join(image_dir, 'button.jpg'), onset=4.2)
    ext = LengthExtractor()
    result = ext.transform(stim).to_df()
    assert 'text_length' in result.columns
    assert result['text_length'][0] == 4
    assert result['onset'][0] == 4.2


@pytest.mark.skipif("'WIT_AI_API_KEY' not in os.environ")
def test_implicit_stim_conversion2():
    audio_dir = join(get_test_data_path(), 'audio')
    stim = AudioStim(join(audio_dir, 'homer.wav'), onset=4.2)
    ext = LengthExtractor()
    result = ext.transform(stim)
    first_word = result[0].to_df()
    assert 'text_length' in first_word.columns
    assert first_word['text_length'][0] > 0
    assert first_word['onset'][0] >= 4.2


@pytest.mark.skipif("'WIT_AI_API_KEY' not in os.environ")
def test_implicit_stim_conversion3():
    video_dir = join(get_test_data_path(), 'video')
    stim = VideoStim(join(video_dir, 'obama_speech.mp4'), onset=4.2)
    ext = LengthExtractor()
    result = ext.transform(stim)
    first_word = result[0].to_df()
    # The word should be "today"
    assert 'text_length' in first_word.columns
    assert first_word['text_length'][0] == 5
    assert first_word['onset'][0] >= 4.2


def test_merge_extractor_results():
    np.random.seed(100)
    image_dir = join(get_test_data_path(), 'image')
    stim1 = ImageStim(join(image_dir, 'apple.jpg'))
    stim2 = ImageStim(join(image_dir, 'obama.jpg'))
    de_names = ['Extractor1', 'Extractor2', 'Extractor3']
    des = [DummyExtractor(name=name) for name in de_names]
    results = [de.transform(stim1) for de in des]
    results += [de.transform(stim2) for de in des]

    df = merge_results(results, format='wide')
    assert df.shape == (200, 17)
    cols = ['onset', 'duration', 'class', 'filename', 'history', 'stim_name',
            'source_file']
    assert not set(cols) - set(df.columns)
    assert 'Extractor2#feature_3' in df.columns

    df = merge_results(results, format='wide', extractor_names='drop')
    assert df.shape == (200, 11)
    assert not set(cols) - set(df.columns)
    assert 'feature_3' in df.columns

    df = merge_results(results, format='wide', extractor_names='multi')
    assert df.shape == (200, 17)
    _cols = [(c, np.nan) for c in cols]
    assert not set(_cols) - set(df.columns)
    assert ('Extractor2', 'feature_3') in df.columns

    with pytest.raises(ValueError):
        merge_results(results, format='long', extractor_names='multi')

    df = merge_results(results, format='long')
    assert df.shape == (1800, 11)
    _cols = cols + ['feature', 'extractor', 'value']
    assert not set(_cols) - set(df.columns)
    row = df.iloc[523, :]
    assert row['feature'] == 'feature_3'
    assert row['value'] == 204
    assert row['extractor'] == 'Extractor2'

    df = merge_results(results, format='long', extractor_names='drop')
    assert df.shape == (1800, 10)
    assert set(_cols) - set(df.columns) == {'extractor'}

    df = merge_results(results, format='long', extractor_names='prepend')
    assert df.shape == (1800, 10)
    row = df.iloc[523, :]
    assert row['feature'] == 'Extractor2#feature_3'
