import pyblish.api
import nuke


class ValidateNeatVideo(pyblish.api.Validator):
    """Fails publish if Neat Video node is present in scene"""

    families = ['deadline.render']
    label = 'Neat Video'
    optional = True

    def process(self, context):

        for node in nuke.allNodes():
            if node.Class().lower().startswith('ofxcom.absoft.neatvideo'):
                msg = 'Neat Video is in file: "%s"' % node.name()
                raise ValueError(msg)
