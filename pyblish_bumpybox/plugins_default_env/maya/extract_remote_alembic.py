import os

import pymel
import pyblish.api

from bait.paths import get_output_path
from bait.deadline import format_frames, get_render_settings, get_deadline_data


class MayaExtractRemoteAlembic(pyblish.api.InstancePlugin):
    """ Extracts alembic files using deadline. """

    order = pyblish.api.ExtractorOrder
    families = ["alembic"]
    optional = True
    label = "Remote Alembic"
    hosts = ["maya"]

    def process(self, instance):

        # Validate whether we can strip namespaces.
        nodes_string = ""
        strip_namespaces = True
        root_names = []

        for member in instance[0]:
            nodes_string += "-root %s " % member.name()
            if member.name().split(":")[-1] not in root_names:
                root_names.append(member.name().split(":")[-1])
            else:
                strip_namespaces = False

        # Generate export command.
        frame_start = int(pymel.core.playbackOptions(q=True, min=True))
        frame_end = int(pymel.core.playbackOptions(q=True, max=True))

        render_settings = get_render_settings("alembic")

        deadline_arguments = {'job': {}, 'plugin': {}}
        deadline_arguments['job']['frames'] = format_frames(frame_start, frame_end)

        if not strip_namespaces:
            msg = "Can't strip namespaces, because of conflicting root names."
            msg += " Nodes will be renamed."
            self.log.warning(msg)

        deadline_arguments['plugin']['StripNamespaces'] = strip_namespaces
        deadline_arguments['plugin']['WriteVisibility'] = nodes_string

        component_name = instance.data["name"]
        version = instance.context.data["version"]
        task_id = instance.context.data['ftrackTask']['id']

        output_path = get_output_path(task_id, component_name, version, ".abc")

        output_dir = os.path.dirname(output_path)
        output_file = os.path.basename(output_path)

        deadline_arguments['plugin']['OutputFilePath'] = output_dir.replace("\\", "/")
        deadline_arguments['plugin']['OutputFile'] = output_file

        self.log.info("Output Dir: {}".format(output_dir))
        self.log.info("Output File: {}".format(output_file))

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Call deadline
        instance.data['families'] += ['deadline']
        instance.data['deadlineData'] = get_deadline_data(render_settings, deadline_arguments)
