import os

import pyblish.api


class CollectScene(pyblish.api.ContextPlugin):
    """ Collecting the scene from the context """
    # offset to get latest currentFile
    order = pyblish.api.CollectorOrder + 0.2

    def process(self, context):

        current_file = context.data('currentFile')
        current_dir = os.path.dirname(current_file)
        publish_dir = os.path.join(current_dir, 'publish')
        publish_file = os.path.join(publish_dir, os.path.basename(current_file))

        self.log.info("Current file: {}".format(current_file))
        self.log.info("Publish file: {}".format(publish_file))

        # create instance
        name = os.path.basename(current_file)
        instance = context.create_instance(name=name)

        instance.set_data('family', value='scene')
        instance.set_data('workPath', value=current_file)
        instance.set_data('publishPath', value=publish_file)

        # ftrack data
        if not context.has_data('ftrackData'):
            return

        ftrack_data = context.data('ftrackData')

        host = pyblish.api.current_host()

        components = {
            '%s_publish' % host: {'path': publish_file},
            '%s_work' % host: {'path': current_file}
        }

        instance.set_data('ftrackComponents', value=components)
        instance.set_data('ftrackAssetType', value='scene')

        asset_name = ftrack_data['Task']['name']
        instance.set_data('ftrackAssetName', value=asset_name)
