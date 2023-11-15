from nbconvert.postprocessors import Postprocessor


class NarrativePostprocessor(Postprocessor):
    def postprocess(self: "NarrativePostprocessor", some_input) -> None:
        print(some_input)
