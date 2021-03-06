import datetime
import logging
import os
import tempfile

import coolname
from octue.cloud import storage
from octue.resources import Datafile, Dataset
from octue.utils.processes import run_subprocess_and_log_stdout_and_stderr


logger = logging.getLogger(__name__)


OUTPUT_EXTENSION = ".bts"
OUTPUT_FILENAME = "TurbSim" + OUTPUT_EXTENSION


def run(analysis):
    """Run a turbsim analysis on the input file specified in the input manifest, writing the output file to the cloud.

    :param octue.resources.Analysis analysis:
    :return None:
    """
    start_datetime = datetime.datetime.now()

    with tempfile.TemporaryDirectory() as temporary_directory:
        input_dataset = analysis.input_manifest.datasets["turbsim"]
        input_dataset.download(temporary_directory)
        input_file = input_dataset.files.one()

        logger.info("Starting turbsim analysis.")
        run_subprocess_and_log_stdout_and_stderr(command=["turbsim", input_file.local_path], logger=logger)

        old_output_filename = os.path.splitext(input_file.local_path)[0] + OUTPUT_EXTENSION

        with tempfile.TemporaryDirectory() as new_temporary_directory:
            new_output_filename = os.path.join(new_temporary_directory, OUTPUT_FILENAME)
            os.rename(old_output_filename, new_output_filename)

            # Instantiate a datafile for the output file.
            with Datafile(path=new_output_filename, mode="a") as (datafile, f):
                datafile.timestamp = start_datetime
                datafile.labels = ["turbsim", "output"]

            analysis.output_manifest.datasets["turbsim"] = Dataset(name="turbsim", path=new_temporary_directory)

            analysis.finalise(
                upload_output_datasets_to=storage.path.join(analysis.output_location, coolname.generate_slug())
            )

    logger.info("Finished turbsim analysis.")
