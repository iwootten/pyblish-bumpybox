import os

import pyblish.api
import pyblish_standalone
import pipeline_schema

from bait.deadline import get_render_settings, get_deadline_data, format_frames
from bait.ftrack.query_runner import QueryRunner


class ExtractCelactionDeadline(pyblish.api.InstancePlugin):

    label = 'Deadline'
    families = ['render']
    order = pyblish.api.ExtractorOrder

    def process(self, instance):

        render_settings = get_render_settings("celaction")

        existing_data = instance.data.get(
            "deadlineData", {"job": {}, "plugin": {}}
        )

        runner = QueryRunner()
        default_pool = runner.get_project_department(instance.context.data["ftrackData"]["Project"]["id"])

        data = get_deadline_data(render_settings, existing_data)
        existing_data["job"]["Pool"] = default_pool
        runner.close_session()

        name = os.path.basename(instance.context.data["currentFile"])
        name = os.path.splitext(name)[0] + " - " + instance.data["name"]
        data["job"]["Name"] = name

        data["job"]['Frames'] = format_frames(instance.data('start'), instance.data('end'))

        # get version data
        version = instance.context.data('version') if instance.context.has_data('version') else 1

        # get output filename
        out_data = pipeline_schema.get_data()
        out_data['extension'] = 'png'
        out_data['output_type'] = 'img'
        out_data['name'] = instance.data["name"]
        out_data['version'] = version
        output_path = pipeline_schema.get_path('output_sequence', out_data)

        data['job']['Plugin'] = 'CelAction'
        data["job"]['OutputFilename0'] = output_path.replace('%04d', '####')

        # plugin data
        render_name_separator = '.'
        path = os.path.dirname(pyblish_standalone.kwargs['path'][0])
        filename = os.path.basename(pyblish_standalone.kwargs['path'][0])
        args = '<QUOTE>%s<QUOTE>' % os.path.join(path, 'publish', filename)
        args += ' -a'

        # not rendering a movie if outputting levels
        # also changing the RenderNameSeparator for better naming
        # ei. "levels.v001_1sky.0001.png" > "levels_1sky.v001.0001.png"
        if instance.has_data('levelSplit'):
            args += ' -l'
            instance.data.pop("movie", None)

            version_string = pipeline_schema.get_path('version', data)
            output_path = output_path.replace('.' + version_string, '')
            data["job"]['OutputFilename0'] = output_path.replace('%04d', '####')

            render_name_separator = '.%s.' % version_string

        args += ' -s <STARTFRAME>'
        args += ' -e <ENDFRAME>'
        args += ' -d <QUOTE>%s<QUOTE>' % os.path.dirname(output_path)
        args += ' -x %s' % instance.data('x')
        args += ' -y %s' % instance.data('y')
        args += ' -r <QUOTE>%s<QUOTE>' % output_path.replace('.%04d', '')
        args += ' -= AbsoluteFrameNumber=on -= PadDigits=4'
        args += ' -= ClearAttachment=on'

        data["plugin"]['Arguments'] = args

        data["plugin"]['StartupDirectory'] = ''
        data["plugin"]['RenderNameSeparator'] = render_name_separator

        # adding to instance
        instance.set_data('deadlineData', value=data)

        # creating output path
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))

        # ftrack data
        components = {instance.data["name"]: {'path': output_path}}
        instance.set_data('ftrackComponents', value=components)
