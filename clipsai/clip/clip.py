"""
Processes a request to transcribe and clip a media file.
"""
# standard library imports
import logging

# current package imports
from .clip_input_validator import ClipInputValidator
from .texttile import TextTileClipFinder
from .clip_model import Clip

# local package imports
from utils.exception_handler import ExceptionHandler
from transcribe.transcription import Transcription


def clip(
    transcription: Transcription,
    device: str = "auto",
    min_clip_time: float = 15,
    max_clip_time: float = 900,
) -> list[Clip]:
    """
    Takes in the transcript of an mp4 or mp3 file and finds engaging audio or
    video clips based on the passed in transcript.

    Parameters
    ----------
    transcription: Transcription
        The transcription of the media file.
    device: str
        The device to use when clipping on. Ex: 'cpu', 'cuda'
    min_clip_time: float
        The minimum clip time in seconds.
    max_clip_time: float
        The maximum clip time in seconds.

    Returns
    -------
    list[Clip]
        A list containing all of the clips found in the media file. Each clip
        contains a start_time, end_time, start_char, and end_char,
        corresponding to the transcript.
    """
    # validate the input request data
    try:
        clip_input_validator = ClipInputValidator()
        exception_handler = ExceptionHandler()
        temp_data = {
            "computeDevice": device,
            "cutoffPolicy": "high",
            "embeddingAggregationPoolMethod": "max",
            "minClipTime": min_clip_time,
            "maxClipTime": max_clip_time,
            "smoothingWidth": 3,
            "windowComparePoolMethod": "mean",
        }
        input_data = clip_input_validator.impute_input_data_defaults(temp_data)
        clip_input_validator.assert_valid_input_data(input_data)
    except Exception as e:
        status_code = exception_handler.get_status_code(e)
        err_msg = str(e)
        stack_trace = exception_handler.get_stack_trace_info()

        error_info = {
            "success": False,
            "status": status_code,
            "message": err_msg,
            "stackTraceInfo": stack_trace,
            "data": input_data,
        }
        logging.error(error_info)
        return error_info

    # run the clip process
    try:
        logging.debug("FINDING ASSET CLIPS")
        clip_finder = TextTileClipFinder(
            device=input_data["computeDevice"],
            min_clip_duration_secs=input_data["minClipTime"],
            max_clip_duration_secs=input_data["maxClipTime"],
            cutoff_policy=input_data["cutoffPolicy"],
            embedding_aggregation_pool_method=input_data[
                "embeddingAggregationPoolMethod"
            ],
            smoothing_width=input_data["smoothingWidth"],
            window_compare_pool_method=input_data["windowComparePoolMethod"],
            save_results=False,
        )
        clip_infos = clip_finder.find_clips(transcription)
        logging.debug("POPULATING LIST OF CLIPS")
        clips = []
        for clip_info in clip_infos:
            clip = Clip(
                clip_info["startTime"],
                clip_info["endTime"],
                clip_info["startChar"],
                clip_info["endChar"]
            )
            clips.append(clip)

        logging.debug("FINISHED CLIPPING MEDIA FILE")
        return clips

    except Exception as e:
        status_code = exception_handler.get_status_code(e)
        err_msg = str(e)
        stack_trace = exception_handler.get_stack_trace_info()

        # define failure information
        error_info = {
            "success": False,
            "status": status_code,
            "message": err_msg,
            "stackTraceInfo": stack_trace,
            "data": input_data,
        }
        logging.error("ERROR INFO FOR FAILED REQUESTR: {}".format(error_info))
        logging.error("DATA FOR FAILED REQUEST: {}".format(input_data))

        return error_info
