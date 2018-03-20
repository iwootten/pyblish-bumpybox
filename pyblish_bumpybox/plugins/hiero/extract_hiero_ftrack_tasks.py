import pyblish.api
import ftrack_api


class ExtractHieroFtrackTasks(pyblish.api.Extractor):
    """ Extract Ftrack tasks.

    Offset to get shot from "extract_ftrack_shot"
    """

    families = ["task"]
    label = "Ftrack Tasks"
    optional = True
    order = pyblish.api.ExtractorOrder + 0.1
    optional = True

    def process(self, instance):

        shot = instance.data["ftrackShot"]
        tasks = shot['children']

        for tag in instance[0].tags():
            data = tag.metadata().dict()
            if "task" == data.get("tag.family", ""):
                task = None

                for t in tasks:
                    if t['name'].lower() == tag.name().lower():
                        task = t

                if not task:
                    try:
                        with ftrack_api.Session() as session:
                            task_type = session.query("Type where name='{}'".format(tag.name())).one()

                            task = session.create('Task', {
                                "name": tag.name().lower(),
                                "parent": shot,
                                "type": task_type
                            })
                            session.commit()
                    except Exception as e:
                        msg = "Could not create task \"{0}\": {1}"
                        self.log.error(msg.format(tag.name().lower(), e))

                if task:
                    # Store task id on tag
                    tag.metadata().setValue("tag.id", task['id'])