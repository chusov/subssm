# -*- coding: utf-8 -*-

"""
Created on 29-03-2013

@author: citan
"""

import os
import os.path
import time
import pickle
import platform
import re
import sys

from subssm.PM import PM
from subssm.PMConnection import PMConnection
from subssm.PMXmlParser import PMXmlParser
from subssm.cu.PMCUParameter import PMCUParameter
from subssm.cu.PMCUContext import PMCUContext


PICKLE_FILE = "data/data.pkl"


def stringSplitByNumbers(x):
    r = re.compile('(\d+)')
    l = r.split(x.get_id())
    return [int(y) if y.isdigit() else y for y in l]


if __name__ == '__main__':

    parser = PMXmlParser()

    supported_parameters = []

    if os.path.isfile(PICKLE_FILE):
        serializedDataFile = open(PICKLE_FILE, "rb")
        defined_parameters = pickle.load(serializedDataFile)
        serializedDataFile.close()
    else:
        defined_parameters = parser.parse("logger_METRIC_EN_v362.xml")
        defined_parameters = sorted(defined_parameters, key=lambda x: x.get_id(), reverse=True)
        output = open(PICKLE_FILE, "wb")
        pickle.dump(defined_parameters, output, -1)
        output.close()

    connection = PMConnection()

    while True:
        try:
            connection.open()
            ecu_packet = connection.init(1)
            tcu_packet = connection.init(2)

            ecu_context = PMCUContext(ecu_packet, [1, 3])
            ecu_parameters = ecu_context.match_parameters(defined_parameters)
            ecu_switch_parameters = ecu_context.match_switch_parameters(defined_parameters)
            ecu_calculated_parameters = ecu_context.match_calculated_parameters(defined_parameters, ecu_parameters)

            tcu_context = PMCUContext(tcu_packet, [2])
            tcu_parameters = tcu_context.match_parameters(defined_parameters)
            tcu_switch_parameters = tcu_context.match_switch_parameters(defined_parameters)
            tcu_calculated_parameters = tcu_context.match_calculated_parameters(defined_parameters, tcu_parameters)

            print("ECU ROM ID: " + ecu_context.get_rom_id())
            print("TCU ROM ID: " + tcu_context.get_rom_id())

            supported_parameters = ecu_parameters + ecu_switch_parameters + ecu_calculated_parameters + tcu_parameters + tcu_switch_parameters + tcu_calculated_parameters

            supported_parameters = sorted(supported_parameters, key=stringSplitByNumbers)

            pids = ["E114", "P104", "P122", "P97"]
            first_window_parameters = []

            for parameter in supported_parameters:
                if parameter.get_id() in pids:
                    pids.remove(parameter.get_id())
                    first_window_parameters.append(parameter)
                    print(parameter.get_address())

            while True:
                packets = connection.read_parameters(first_window_parameters)
                print(f'@ {packets}')

        except IOError as e:
            print('I/O error: {0} {1}'.format(e.errno, e.strerror))
            if connection is not None:
                connection.close()
                time.sleep(3)
            continue
