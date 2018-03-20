import pyblish.api
import os


class ExtractMovie(pyblish.api.InstancePlugin):
    """ Extracts movie from image sequence. """

    families = ["img"]
    order = pyblish.api.ExtractorOrder + 0.4
    label = "Movie"
    optional = True
    active = True

    def process(self, instance):

        if "remote" not in instance.data.get("families", []):
            return

        # skipping instance if data is missing
        if "deadlineData" not in instance.data:
            msg = "No deadlineData present. Skipping \"%s\"" % instance
            self.log.info(msg)
            return

        collection = instance.data["collection"]

        start_index = str(list(collection.indexes)[0])

        job_data = instance.data["deadlineData"]["job"]

        extra_info_key_value = {}

        input_args = "-y -gamma 2.2 -framerate 25 -start_number {}".format(start_index)
        extra_info_key_value["FFMPEGInputArgs0"] = input_args

        output_file = job_data["OutputFilename0"]
        input_file = output_file.replace("####", "%04d")

        output_basename, output_ext = os.path.splitext(output_file)
        output_basename = output_basename.strip("#")

        if 'audio' in instance.context.data and instance.context.data['audio']['enabled']:
            audio_file = instance.context.data['audio']['filename']
            self.log.debug("Applying audio: {0}".format(audio_file))

            input_file += " -i " + audio_file.replace("\\", "/")

        extra_info_key_value["FFMPEGInput0"] = input_file

        output_args = "-q:v 0 -pix_fmt yuv420p -vf scale=trunc(iw/2)*2:trunc(ih/2)*2,colormatrix=bt601:bt709 " \
                      "-timecode 00:00:00:01"

        extra_info_key_value["FFMPEGOutputArgs0"] = output_args
        extra_info_key_value["FFMPEGOutput0"] = "{}{}".format(output_basename, "0001.mov")

        instance.data["deadlineData"]["job"]["ExtraInfoKeyValue"] = extra_info_key_value

