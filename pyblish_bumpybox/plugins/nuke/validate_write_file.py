import os

import pyblish.api
import nuke
from bait.paths import get_output_path


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

            path = os.path.dirname(nuke.filename(instance[0]))
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
        task_id = instance.context.data["ftrackData"]["Task"]["id"]
        component_name = instance[0].name()
        version = instance.context.data["version"]

        current = nuke.filename(instance[0])

        # Extension, defaulting to exr files.
        _, ext = os.path.splitext(current)

        if not ext:
            ext = ".exr"

        output_dir = os.path.dirname(get_output_path(task_id, component_name, version, ext))
        output_sequence, _ = os.path.splitext(os.path.basename(nuke.scriptName()))

        output_sequence += ".%{1}d{2}".format(
            instance[0].name(),
            str(4).zfill(2),
            ext
        )

        return output_dir + "/" + output_sequence
