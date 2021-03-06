/*
    Copyright (c) 2011, Jun Namikawa <jnamika@gmail.com>

    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted, provided that the above
    copyright notice and this permission notice appear in all copies.

    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
    WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
    MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
    ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
    WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
    ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
    OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <assert.h>

#include "utils.h"
#include "rnn_runner2.h"


/******************************************************************************/
/********** Initialization and Free *******************************************/
/******************************************************************************/


int _new_rnn_runner2 (struct rnn_runner2 **runner)
{
    (*runner) = malloc(sizeof(struct rnn_runner2));
    if ((*runner) == NULL) {
        return 1;
    }
    return 0;
}

void _delete_rnn_runner2 (struct rnn_runner2 *runner)
{
    free(runner);
}




void init_rnn_runner2 (
        struct rnn_runner2 *runner,
        FILE *fp,
        int window_length)
{
    assert(window_length > 0);
    FREAD(&runner->delay_length, 1, fp);
    fread_recurrent_neural_network(&runner->rnn, fp);
    rnn_add_target(&runner->rnn, window_length + runner->delay_length, NULL,
            NULL);
    runner->id = runner->rnn.series_num - 1;
    runner->rnn.rnn_p.fixed_weight = 1;
    runner->rnn.rnn_p.fixed_threshold = 1;
    runner->rnn.rnn_p.fixed_tau = 1;
    runner->rnn.rnn_p.fixed_init_c_state = 0;
}


void init_rnn_runner2_with_filename (
        struct rnn_runner2 *runner,
        const char *filename,
        int window_length)
{
    FILE *fp;
    fp = fopen(filename, "rb");
    if (fp != NULL) {
        init_rnn_runner2(runner, fp, window_length);
        fclose(fp);
    } else {
        print_error_msg("cannot open %s", filename);
        exit(EXIT_FAILURE);
    }
}


void free_rnn_runner2 (struct rnn_runner2 *runner)
{
    free_recurrent_neural_network(&runner->rnn);
}


static void copy_init_state (
        struct rnn_state *dst,
        struct rnn_state *src)
{
    for (int n = 0; n < dst->length; n++) {
        if (n < src->length) {
            memmove(dst->in_state[n], src->in_state[n], sizeof(double) *
                    dst->rnn_p->in_state_size);
        } else {
            for (int i = 0; i < dst->rnn_p->in_state_size; i++) {
                dst->in_state[n][i] = (2*genrand_real3()-1);
            }
        }
    }
    memmove(dst->init_c_state, src->init_c_state, sizeof(double) *
            dst->rnn_p->c_state_size);
    memmove(dst->init_c_inter_state, src->init_c_inter_state, sizeof(double) *
            dst->rnn_p->c_state_size);
}

static void random_init_state (struct rnn_state *rnn_s)
{
    for (int n = 0; n < rnn_s->length; n++) {
        for (int i = 0; i < rnn_s->rnn_p->in_state_size; i++) {
            rnn_s->in_state[n][i] = (2*genrand_real3()-1);
        }
    }
    for (int i = 0; i < rnn_s->rnn_p->c_state_size; i++) {
        rnn_s->init_c_state[i] = (2*genrand_real3()-1);
        rnn_s->init_c_inter_state[i] = atanh(rnn_s->init_c_state[i]);
    }
}


void set_init_state_of_rnn_runner2 (
        struct rnn_runner2 *runner,
        int series_id)
{
    if (series_id >= 0 && series_id < runner->id) {
        copy_init_state(runner->rnn.rnn_s + runner->id, runner->rnn.rnn_s +
                series_id);
    } else {
        random_init_state(runner->rnn.rnn_s + runner->id);
    }
}


/******************************************************************************/
/********** Computation of forward dynamics ***********************************/
/******************************************************************************/


static void rnn_fmap (
        struct rnn_state *rnn_s,
        int delay_length)
{
    const struct rnn_parameters *rnn_p = rnn_s->rnn_p;

    rnn_forward_backward_dynamics(rnn_s);

    memmove(rnn_s->init_c_inter_state, rnn_s->c_inter_state[0], sizeof(double) *
            rnn_p->c_state_size);
    memmove(rnn_s->init_c_state, rnn_s->c_state[0], sizeof(double) *
            rnn_p->c_state_size);
    for (int n = 1; n < rnn_s->length; n++) {
        memmove(rnn_s->teach_state[n-1], rnn_s->teach_state[n], sizeof(double) *
                rnn_p->out_state_size);
        memmove(rnn_s->in_state[n-1], rnn_s->in_state[n], sizeof(double) *
                rnn_p->in_state_size);
        memmove(rnn_s->c_inter_state[n-1], rnn_s->c_inter_state[n],
                sizeof(double) * rnn_p->c_state_size);
        memmove(rnn_s->c_state[n-1], rnn_s->c_state[n], sizeof(double) *
                rnn_p->c_state_size);
    }
}


void update_rnn_runner2 (
        struct rnn_runner2 *runner,
        double *input,
        int reg_count,
        double rho_init,
        double momentum)
{
    struct rnn_state *rnn_s = runner->rnn.rnn_s + runner->id;

    if (input != NULL) {
        memmove(rnn_s->in_state[rnn_s->length - 1], input, sizeof(double) *
                rnn_s->rnn_p->in_state_size);
        memmove(rnn_s->teach_state[rnn_s->length - runner->delay_length - 1],
                input, sizeof(double) * rnn_s->rnn_p->out_state_size);
    }

    int tmp_length = rnn_s->length;
    rnn_s->length -= runner->delay_length;
    for (int i = 0; i < reg_count; i++) {
        rnn_forward_backward_dynamics(rnn_s);
        rnn_update_delta_init_c_inter_state(rnn_s, momentum);
        rnn_update_init_c_inter_state(rnn_s, rho_init);
    }
    rnn_s->length = tmp_length;
    rnn_fmap(rnn_s, runner->delay_length);
}



/******************************************************************************/
/********** Interface *********************************************************/
/******************************************************************************/

int rnn_in_state_size_from_runner2 (struct rnn_runner2 *runner)
{
    return runner->rnn.rnn_p.in_state_size;
}

int rnn_c_state_size_from_runner2 (struct rnn_runner2 *runner)
{
    return runner->rnn.rnn_p.c_state_size;
}

int rnn_out_state_size_from_runner2 (struct rnn_runner2 *runner)
{
    return runner->rnn.rnn_p.out_state_size;
}

int rnn_delay_length_from_runner2 (struct rnn_runner2 *runner)
{
    return runner->delay_length;
}

int rnn_window_length_from_runner2 (struct rnn_runner2 *runner)
{
    return runner->rnn.rnn_s[runner->id].length - runner->delay_length;
}

int rnn_output_type_from_runner2 (struct rnn_runner2 *runner)
{
    return (int)runner->rnn.rnn_p.output_type;
}

int rnn_target_num_from_runner2 (struct rnn_runner2 *runner)
{
    return runner->id;
}

double* rnn_in_state_from_runner2 (struct rnn_runner2 *runner)
{
    const int n = runner->rnn.rnn_s[runner->id].length - 1;
    return runner->rnn.rnn_s[runner->id].in_state[n];
}

double* rnn_c_state_from_runner2 (struct rnn_runner2 *runner)
{
    const int n = runner->rnn.rnn_s[runner->id].length - 1;
    return runner->rnn.rnn_s[runner->id].c_state[n];
}

double* rnn_c_inter_state_from_runner2 (struct rnn_runner2 *runner)
{
    const int n = runner->rnn.rnn_s[runner->id].length - 1;
    return runner->rnn.rnn_s[runner->id].c_inter_state[n];
}

double* rnn_out_state_from_runner2 (struct rnn_runner2 *runner)
{
    const int n = runner->rnn.rnn_s[runner->id].length - 1;
    return runner->rnn.rnn_s[runner->id].out_state[n];
}

double* rnn_var_state_from_runner2 (struct rnn_runner2 *runner)
{
    const int n = runner->rnn.rnn_s[runner->id].length - 1;
    return runner->rnn.rnn_s[runner->id].var_state[n];
}

struct rnn_state* rnn_state_from_runner2 (struct rnn_runner2 *runner)
{
    return runner->rnn.rnn_s + runner->id;
}

