import os
import shutil

import pyblish.api
import pyblish_standalone
from bait.paths import get_env_work_file


class RepairScenePath(pyblish.api.Action):
    label = "Repair"
    icon = "wrench"
    on = "failed"

    def process(self, context, plugin):

        # get version data
        version = context.data('version') if context.has_data('version') else 1

        task_id = context.data["ftrackData"]["Task"]["id"]
        expected_path = get_env_work_file("celaction", task_id, "scn", version)

        if os.path.exists(expected_path):
            msg = "\"{0}\" already exists. Please repair manually."
            raise ValueError(msg.format(expected_path))
        else:
            expected_dir = os.path.dirname(expected_path)
            if not os.path.exists(expected_dir):
                os.makedirs(expected_dir)

            src = pyblish_standalone.kwargs['path'][0]

            shutil.copy(src, expected_path)

            pyblish_standalone.kwargs['path'] = [expected_path]
            context.data["currentFile"] = expected_path

            self.log.info("Saved to \"%s\"" % expected_path)


class ValidateScenePath(pyblish.api.InstancePlugin):
    order = pyblish.api.ValidatorOrder
    families = ['scene']
    label = 'Scene Path'
    actions = [RepairScenePath]

    def process(self, instance):

        # getting current work file
        current_scene_path = pyblish_standalone.kwargs['path'][0]

        version = instance.context.data('version') if instance.context.has_data('version') else 1

        task_id = instance.context.data["ftrackData"]["Task"]["id"]
        expected_scene_path = get_env_work_file("celaction", task_id, "scn", version)

        msg = 'Scene path is not correct: Current: {}, Expected: {}'.format(current_scene_path, expected_scene_path)

        assert expected_scene_path == current_scene_path, msg
