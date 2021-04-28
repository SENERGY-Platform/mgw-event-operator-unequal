#  Copyright 2021 InfAI (CC SES)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from senergy_local_analytics import App, Input, Output, Config
import converter
import typing
import json
import os
import requests


class Operator:

    def __init__(self, converter_lib_location):
        self.converter = converter.Converter(converter_lib_location)

    def process(self, inputs: typing.List[Input], config: Config):
        from_characteristic = config.get_config_value("convertFrom")
        to_characteristic = config.get_config_value("convertTo")
        config_value = json.loads(config.get_config_value("value"))
        engine_url = config.get_config_value("url")
        event_id = config.get_config_value("eventId")
        input_value = inputs[0].current_value
        value = input_value
        if from_characteristic != "" and to_characteristic != "" and from_characteristic != to_characteristic:
            cast_result = self.converter.cast(input_value, from_characteristic, to_characteristic)
            if not isinstance(cast_result, dict):
                print("ERROR: cast result = {}".format(cast_result))
            if "err" in cast_result and not cast_result["err"]:
                print("ERROR: cast result = {}".format(cast_result))
                return Output(False, {})
            if "result" not in cast_result:
                print("ERROR: cast result = {}".format(cast_result))
                return Output(False, {})
            value = cast_result["result"]

        if input_value is not None and self.check(config_value, value):
            self.trigger(engine_url, event_id, value)

        return Output(False, {})

    def get_converter(self):
        return self.converter

    def check(self, config_value, input_value):
        print("check: {}, {}, {}".format(config_value, input_value, config_value == input_value))
        return config_value != input_value

    def trigger(self, engine_url, event_id, output_value):
        print("trigger: {}, {}, {}".format(engine_url, event_id, output_value))
        payload = {
            'messageName': event_id,
            'all': True,
            'resultEnabled': False,
            'processVariablesLocal': {
                'event': {
                    'value': output_value
                }
            }
        }
        x = requests.post(engine_url, json=payload, headers={'content-type': 'application/json'})
        if not x.ok:
            print("ERROR: {} {}".format(x.status_code, x.text))


if __name__ == '__main__':
    app = App()

    input1 = Input("value")
    app.config([input1])

    operator = Operator(os.getenv('CONVERTER_LIB_LOCATION'))
    print("start operator")
    app.process_message(operator.process)
    app.main()
