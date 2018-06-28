"""
Most of these functions were copied by Dolf from Dolf's Masters project with permission of Dolf.
"""

import numpy as np
from scipy.io import wavfile
import pyfftw

pyfftw.interfaces.cache.enable()
discrete_convolution_fft_cache = {}


def discrete_convolution(x, h):
    with np.errstate(all='raise'):

        if not np.all(np.isfinite(x)):
            raise ValueError("Input signal x contains non-finite values.")
        if not np.all(np.isfinite(h)):
            raise ValueError("Input signal h contains non-finite values.")

        n_fft_min = len(x) + len(h) - 1
        n_fft = smallest_power_of_two_greater_than(n_fft_min)

        if n_fft not in discrete_convolution_fft_cache:
            rfft_input = pyfftw.empty_aligned(n_fft, dtype='float64')
            rfft_func = pyfftw.builders.rfft(rfft_input, overwrite_input=True)
            irfft_input = pyfftw.empty_aligned((n_fft // 2) + 1, dtype='complex128')
            irfft_func = pyfftw.builders.irfft(irfft_input, overwrite_input=True)
            discrete_convolution_fft_cache[n_fft] = (rfft_input, rfft_func, irfft_input, irfft_func)
        else:
            rfft_input, rfft_func, irfft_input, irfft_func = discrete_convolution_fft_cache[n_fft]

        rfft_input[:len(x)] = x
        rfft_input[len(x):] = 0
        x_fft = np.copy(rfft_func())  # Need to copy here, since the next call to rfft_func overwrites the output
        rfft_input[:len(h)] = h
        rfft_input[len(h):] = 0
        h_fft = rfft_func()

        irfft_input[:] = np.copy(x_fft * h_fft)
        return np.copy(irfft_func()[:n_fft_min])


def cross_correlation(x, h):
    return discrete_convolution(x, h[::-1])


def cross_correlation_sample_axis(x, h):
    b = np.arange(len(x))[1:]
    a = -np.arange(len(h))[::-1]
    return np.concatenate((a, b))


def cross_correlation_time_axis(x, h, sample_rate):
    return cross_correlation_sample_axis(x, h) / float(sample_rate)


def windows(
        signal,
        window_size,
        step_size,
        axis=-1,
        allow_float=False,
        include_short_windows=False,
        min_window_length=1,
):
    """


    Break the given signal into overlapping windows, and yield those windows.
    This function does not apply an apodization.
    If the signal length is not equal to the window size + a multiple of the step size, some samples at the end of the
    signal might be unused.

    :param list|np.ndarray signal: An array for which to return windows.

    :param int|float window_size: The number of array elements in each window.

    :param int|float step_size: The number of array elements between the start of one window, and the start of the next
        window.

    :param int axis: The axis along which to slice. Defaults to -1, which is the last axis.

    :param bool allow_float: If this is False, window_size and step_size must be integers.

    :param bool include_short_windows: The last few windows will usually be shorter than the rest, since the end of the
        window is after the end of the signal. To discard those windows, make this False.

    :param int min_window_length: Only yield windows that are at least as long as this number.

    :return: A generator which yields bits of the signal array at a time.

    >>> list(windows(signal=range(4), window_size=2, step_size=1))
    [[0, 1], [1, 2], [2, 3]]

    >>> list(windows(signal=range(4), window_size=3, step_size=1))
    [[0, 1, 2], [1, 2, 3]]

    >>> list(windows(signal=range(4), window_size=4, step_size=1))
    [[0, 1, 2, 3]]

    >>> list(windows(signal=range(4), window_size=2, step_size=2))
    [[0, 1], [2, 3]]

    >>> list(windows(signal=range(4), window_size=3, step_size=2))
    [[0, 1, 2]]

    >>> list(windows(signal=range(4), window_size=3, step_size=2, include_short_windows=True))
    [[0, 1, 2], [2, 3]]

    >>> list(windows(signal=range(4), window_size=3, step_size=2, include_short_windows=True, min_window_length=2))
    [[0, 1, 2], [2, 3]]

    >>> list(windows(signal=range(4), window_size=3, step_size=2, include_short_windows=True, min_window_length=3))
    [[0, 1, 2]]

    >>> list(windows(signal=range(4), window_size=4, step_size=2))
    [[0, 1, 2, 3]]

    >>> a = np.linspace(0, 14, 15).reshape(5,3)
    >>> a
    array([[ 0.,  1.,  2.],
           [ 3.,  4.,  5.],
           [ 6.,  7.,  8.],
           [ 9., 10., 11.],
           [12., 13., 14.]])
    >>> np.array(list(windows(signal=a, window_size=2, step_size=1)))
    array([[[ 0.,  1.],
            [ 3.,  4.],
            [ 6.,  7.],
            [ 9., 10.],
            [12., 13.]],
    <BLANKLINE>
           [[ 1.,  2.],
            [ 4.,  5.],
            [ 7.,  8.],
            [10., 11.],
            [13., 14.]]])

    >>> np.array(list(windows(signal=a, window_size=2, step_size=1, axis=0)))
    array([[[ 0.,  1.,  2.],
            [ 3.,  4.,  5.]],
    <BLANKLINE>
           [[ 3.,  4.,  5.],
            [ 6.,  7.,  8.]],
    <BLANKLINE>
           [[ 6.,  7.,  8.],
            [ 9., 10., 11.]],
    <BLANKLINE>
           [[ 9., 10., 11.],
            [12., 13., 14.]]])

    >>> l = list(windows(signal=a, window_size=3, step_size=2, include_short_windows=True))
    >>> len(l)
    2
    >>> l[0]
    array([[ 0.,  1.,  2.],
           [ 3.,  4.,  5.],
           [ 6.,  7.,  8.],
           [ 9., 10., 11.],
           [12., 13., 14.]])
    >>> l[1]
    array([[ 2.],
           [ 5.],
           [ 8.],
           [11.],
           [14.]])

    >>> l = list(windows(signal=a, window_size=3, step_size=2, include_short_windows=False))
    >>> len(l)
    1
    >>> l[0]
    array([[ 0.,  1.,  2.],
           [ 3.,  4.,  5.],
           [ 6.,  7.,  8.],
           [ 9., 10., 11.],
           [12., 13., 14.]])
    """

    if type(signal) is list:
        for i_start, i_end in window_indices(
                n_samples=len(signal),
                window_size=window_size,
                step_size=step_size,
                allow_float=allow_float,
                include_short_windows=include_short_windows,
                min_window_length=min_window_length,
        ):
            yield signal[i_start:i_end]

    elif isinstance(signal, np.ndarray):
        n_dims = len(signal.shape)
        if type(axis) is not int:
            raise TypeError("axis must be an integer.")
        if axis >= n_dims or axis < -n_dims:
            raise ValueError(
                "The input signal only has {} dimensions, so axis must be in the range [{}, {}]. We got {}.".format(
                    n_dims,
                    -n_dims,
                    n_dims - 1,
                    axis
                )
            )

        snit = [slice(None)] * n_dims
        for i_start, i_end in window_indices(
                n_samples=signal.shape[axis],
                window_size=window_size,
                step_size=step_size,
                allow_float=allow_float,
                include_short_windows=include_short_windows,
                min_window_length=min_window_length,
        ):
            snit[axis] = slice(i_start, i_end)
            yield signal[snit]

    else:
        raise TypeError("signal should be a list or an ndarray.")


def window_indices(
        n_samples,
        window_size,
        step_size,
        allow_float=False,
        include_short_windows=False,
        min_window_length=1,
):
    """
    Copied from Dolf's Masters project

    Calculate the slice indices

    :param int n_samples: The length of the signal to slice.

    :param int|float window_size: The number of array elements in each window.

    :param int|float step_size: The number of array elements between the start of one window, and the start of the next
        window.

    :param bool allow_float: If this is False, window_size and step_size must be integers.

    :param bool include_short_windows: The last few windows will usually be shorter than the rest, since the end of the
        window is after the end of the signal. To discard those windows, make this False.

    :param int min_window_length: Only yield windows that are at least as long as this number.

    :return: A generator that yields tuples with (start, stop) indices for slicing signals.

    >>> list(window_indices(10, 5, 3))
    [(0, 5), (3, 8)]

    >>> list(window_indices(10, 5, 3, include_short_windows=True))
    [(0, 5), (3, 8), (6, 10), (9, 10)]

    >>> list(window_indices(10, 5, 3, include_short_windows=True, min_window_length=2))
    [(0, 5), (3, 8), (6, 10)]

    >>> list(window_indices(10, 5, 3, include_short_windows=True, min_window_length=4))
    [(0, 5), (3, 8), (6, 10)]

    >>> list(window_indices(10, 5, 3, include_short_windows=True, min_window_length=5))
    [(0, 5), (3, 8)]

    >>> list(window_indices(10, 5, 3.3, allow_float=True))
    [(0, 5), (3, 8)]

    >>> list(window_indices(10, 5, 3.3, allow_float=True, include_short_windows=True))
    [(0, 5), (3, 8), (7, 10)]

    >>> list(window_indices(10, 3.7, 2.1, allow_float=True, include_short_windows=True))
    [(0, 4), (2, 6), (4, 8), (6, 10), (8, 10)]

    >>> list(window_indices(10, 3.7, 2.1, allow_float=True))
    [(0, 4), (2, 6), (4, 8), (6, 10)]

    """

    if type(n_samples) is not int:
        raise TypeError("Number of samples must be an integer.")

    if not allow_float:
        if type(window_size) is not int:
            raise TypeError("Window size must be an integer if allow_float==False.")
        if type(step_size) is not int:
            raise TypeError("Step size must be an integer if allow_float==False.")

    i_start = 0
    i_end = window_size
    while int(round(i_start)) <= n_samples - 1:

        if round(i_end) > n_samples:
            if include_short_windows:
                i_end = n_samples
            else:
                break

        a = int(round(i_start))
        b = int(round(i_end))
        if b - a >= min_window_length:
            yield a, b

        i_start += step_size
        i_end += step_size


def energy(signal, axis=-1):
    return np.mean(np.abs(signal), axis=axis)


def window_energy(signal, sample_rate, window_duration=1., axis=-1):
    window_n_samples = int(window_duration * sample_rate)
    return (energy(w, axis=axis) for w in windows(
        signal=signal,
        window_size=window_n_samples,
        step_size=window_n_samples,  # no overlap
        axis=axis,
    ))


def window_energy_from_file(input_filename, window_duration=1.):
    audio_fs, audio_data = wavfile.read(filename=input_filename, mmap=True)
    return np.array(list(window_energy(audio_data, audio_fs, window_duration=window_duration, axis=0)))


def correlate_audio_files(input_filename1, input_filename2, window_duration=1., channel=0):
    e1 = window_energy_from_file(input_filename1, window_duration=window_duration)[:, channel]
    e2 = window_energy_from_file(input_filename2, window_duration=window_duration)[:, channel]
    conv = cross_correlation(e1, e2)
    t_conv = cross_correlation_time_axis(e1, e2, sample_rate=1./window_duration)

    return t_conv, conv


def smallest_power_of_two_greater_than(x):
    return int(2 ** np.ceil(np.log2(int(x))))
