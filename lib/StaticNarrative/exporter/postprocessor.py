from nbconvert.postprocessors import Postprocessor


class NarrativePostprocessor(Postprocessor):
    def postprocess(self, input):
        print(input)
