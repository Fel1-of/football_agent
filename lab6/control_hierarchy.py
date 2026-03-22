class ControllerLayer:
    """
    Базовый слой иерархического контроллера.
    Каждый слой получает данные, может их дополнить и передать выше.
    """

    def __init__(self):
        self.memory = {}

    def execute(self, input_data, upper_layers):
        current = self.process(input_data)

        if upper_layers:
            next_layer = upper_layers[0]
            rest = upper_layers[1:]
            upper_result = next_layer.execute(current, rest)
            return self.merge(current, upper_result)

        return self.finalize(current)

    def process(self, input_data):
        return input_data

    def merge(self, current_result, upper_result):
        if upper_result is not None:
            return upper_result
        return current_result

    def finalize(self, result):
        return result
