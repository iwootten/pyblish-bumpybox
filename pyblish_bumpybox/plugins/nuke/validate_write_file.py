import os

import pyblish.api
import nuke


class BumpyboxNukeRepairWriteFile(pyblish.api.Action):

    label = "Repair"
    icon = "wrench"
    on = "failed"

    def process(self, context, plugin):

        # Get the errored instances
        failed = []
        for result in context.data["results"]:
            if (result["error"] is not None and result["instance"] is not None
               and result["instance"] not in failed):
                failed.append(result["instance"])

        # Apply pyblish.logic to get the instances for the plug-in
        instances = pyblish.api.instances_by_plugin(failed, plugin)

        for instance in instances:

            cls_instance = BumpyboxNukeValidateWriteFile()
            value = cls_instance.get_expected_value(instance)
            instance[0]["file"].setValue(value)

            ext = os.path.splitext(value)[1]
            instance[0]["file_type"].setValue(ext[1:])

            path = os.path.dirname(instance[0]["file"].evaluate())
            if not os.path.exists(path):
                os.makedirs(path)


class BumpyboxNukeValidateWriteFile(pyblish.api.InstancePlugin):
    """ Validates file output. """

    order = pyblish.api.ValidatorOrder
    optional = True
    families = ["write"]
    label = "Write File"
    actions = [BumpyboxNukeRepairWriteFile]
    hosts = ["nuke"]

    def process(self, instance):

        current = instance[0]["file"].getValue()
        expected = self.get_expected_value(instance)

        msg = "Output path for \"{0}\"."
        msg += "Current: \"{1}\". Expected: \"{2}\""
        assert current == expected, msg.format(
            instance[0].name(), current, expected
        )

        # Validate output directory exists
        path = os.path.dirname(instance[0]["file"].evaluate())
        msg = "Output directory doesn't exist: \"{0}\"".format(path)
        assert os.path.exists(path), msg

    def get_expected_value(self, instance):
        expected = nuke.script_directory() + "/workspace/"

        current = instance[0]["file"].getEvaluatedValue()
        current_file = instance.context.data["currentFile"]

        # Default padding starting at 4 digits.
        padding = 4
        if instance.data["collection"]:
            padding = instance.data["collection"].padding
        # Can't have less than 4 digits.
        if padding < 4:
            padding = 4

        # Extension, defaulting to exr files.
        ext = os.path.splitext(os.path.basename(current))[1]
        if not ext:
            ext = ".exr"

        expected += "{0}_{1}.%{2}d{3}".format(
            os.path.splitext(os.path.basename(current_file))[0],
            instance[0].name(),
            str(padding).zfill(2),
            ext
        )
        return expected
