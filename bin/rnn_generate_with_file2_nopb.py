# -*- coding:utf-8 -*-

import sys
import os
import re
import rnn_runner2

def main():
    seed = 0
    sequence = int(sys.argv[1]) if str.isdigit(sys.argv[1]) else 0
    ignore_index = [int(x) for x in sys.argv[2].split(',') if str.isdigit(x)]
    type = sys.argv[3]
    window_length = int(sys.argv[4]) if str.isdigit(sys.argv[4]) else 10
    reg_count = int(sys.argv[5]) if str.isdigit(sys.argv[5]) else 0
    try:
        rho_init = float(sys.argv[6])
    except ValueError:
        rho_init = 0.001
    try:
        moment = float(sys.argv[7])
    except ValueError:
        moment = 0

    '''
    try: 
        gamma_bp = float(sys.argv[8])
    except ValueError:
        gamma_bp = 1.0
    try: 
        gamma_top = float(sys.argv[9])
    except ValueError:
        gamma_top = 0
    try:
        beta = float(sys.argv[10])
    except ValueError:
        beta = 1.0
    
    rnn_file = sys.argv[11]
    sequence_file = sys.argv[12]
    '''
    rnn_file = sys.argv[8]
    sequence_file = sys.argv[9]


    rnn_runner2.init_genrand(seed)
    runner = rnn_runner2.RNNRunner()
    runner.init(rnn_file, window_length)
    runner.set_time_series_id(sequence)

    p = re.compile(r'(^#)|(^$)')
    out_state_queue = []
    time_step = 0
    for line in open(sequence_file, 'r'):
        if p.match(line) == None:
            input = map(float, line[:-1].split())
            target = list(input)
            if len(out_state_queue) >= runner.delay_length():
                out_state = out_state_queue.pop(0)
                for i in ignore_index:
                    input[i] = out_state[i]
            runner.update(sequence, time_step, input, reg_count, rho_init, moment)
            #runner.update(sequence, time_step, input, reg_count, rho_init, moment, gamma_bp, gamma_top, beta)
            out_state = runner.out_state()
            out_state_queue.append(out_state)
            if type == 'o':
                print '\t'.join([str(x) for x in out_state])
            elif type == 'c':
                c_state = runner.c_state()
                print '\t'.join([str(x) for x in c_state])
            elif type == 'a':
                var_state = runner.var_state()
                c_inter_state = runner.c_inter_state()
                #print '\t'.join([str(x) for x in input + out_state + var_state + c_inter_state])
                print '\t'.join([str(x) for x in target + out_state + var_state + c_inter_state])
            time_step += 1

if __name__ == '__main__':
    main()

