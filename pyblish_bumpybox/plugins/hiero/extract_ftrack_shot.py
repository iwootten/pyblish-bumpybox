import pyblish.api

from bait.ftrack.query_runner import QueryRunner


class BumpyboxHieroExtractFtrackShot(pyblish.api.InstancePlugin):
    """ Creates ftrack shots by the name of the shot. """

    order = pyblish.api.ExtractorOrder
    families = ["ftrack", "trackItem"]
    match = pyblish.api.Subset
    label = "Ftrack Shot"
    optional = True
    query_runner = QueryRunner()

    def parse_shot_elements(self, item_name):
        episode_name = False
        sequence_name = False
        shot_name = False

        if "--" in item_name:
            name_split = item_name.split("--")

            if len(name_split) == 3:
                episode_name = name_split[0]
                sequence_name = name_split[1]
                shot_name = name_split[2]

            if len(name_split) == 2:
                sequence_name = name_split[0]
                shot_name = name_split[1]

        return {
            "episode_name": episode_name,
            "sequence_name": sequence_name,
            "shot_name": shot_name
        }

    def filter_for_object(self, parent_list, entity_type):
        return next((item for item in parent_list if 'object_type' in item and
                    item['object_type']['name'] == entity_type), None)

    def create_path_to_shot(self, parents, shot_elements):
        # First assign to project entity
        project = parents[0]

        episode = self.filter_for_object(parents, 'Episode')
        sequence = self.filter_for_object(parents, 'Sequence')
        shot = self.filter_for_object(parents, 'Shot')

        if shot_elements['episode_name'] and project and not episode:
            episode = self.query_runner.create_episode(project, shot_elements['episode_name'])

        if shot_elements['sequence_name'] and episode and not sequence:
            sequence = self.query_runner.get_or_create_sequence(episode, shot_elements['sequence_name'])

        if shot_elements['shot_name'] and sequence and not shot:
            shot = self.query_runner.get_or_create_shot(sequence, shot_elements['shot_name'])

        return shot

    def get_or_create_shot(self, instance):

        ftrack_data = instance.context.data("ftrackData")
        task = self.query_runner.get_task(ftrack_data["Task"]["id"])

        item = instance[0]

        shot_elements = self.parse_shot_elements(item.name())
        parents = self.query_runner.get_parents(task)

        self.log.info("Parents " + str(parents))
        self.log.info("Shot elements " + str(shot_elements))

        # Setup all the parents to this task
        shot = self.create_path_to_shot(parents, shot_elements)

        return shot

    def process(self, instance):

        item = instance[0]

        # Get/Create shot
        shot = None
        for tag in item.tags():
            if tag.name() == "ftrack":
                metadata = tag.metadata()

                if 'tag.id' in metadata:
                    shot = self.query_runner.get_shot(metadata["tag.id"])
                else:
                    shot = self.get_or_create_shot(instance)

        instance.data["ftrackShotId"] = shot['id']
        instance.data["ftrackShot"] = shot

        # Store shot id on tag
        for tag in item.tags():
            if tag.name() == "ftrack":
                tag.metadata().setValue("tag.id", shot['id'])

        # Assign attributes to shot.
        sequence = item.parent().parent()

        shot['custom_attributes']["fstart"] = 1
        shot['custom_attributes']["fps"] = sequence.framerate().toFloat()

        duration = item.sourceOut() - item.sourceIn()
        duration = abs(int(round((abs(duration) + 1) / item.playbackSpeed())))
        shot['custom_attributes']["fend"] = duration

        try:
            fmt = sequence.format()
            shot['custom_attributes']["width"] = fmt.width()
            shot['custom_attributes']["height"] = fmt.height()
        except Exception as e:
            self.log.warning("Could not set the resolution: " + str(e))

        # Get handles.
        handles = 0

        if "handles" in instance.data["families"]:
            for tag in instance.data["tagsData"]:
                if "handles" == tag.get("tag.family", ""):
                    handles = int(tag["tag.value"])

        instance.data["handles"] = handles

        shot['custom_attributes']["handles"] = handles

        self.query_runner.commit()
