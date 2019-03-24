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

    //struct rnn_state *rnn_s_reg = runner->rnn.rnn_s + runner->id;
    //MALLOC2(rnn_s_reg->assigned_pb, runner->id, runner->rnn.rnn_p.pb_num);
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
    struct rnn_state *rnn_s_reg = runner->rnn.rnn_s + runner->id;
    struct rnn_parameters *rnn_p = rnn_s_reg->rnn_p;
    
    rnn_p->pb_num = 0;
    for (int i = 0; i < rnn_p->c_state_size; i++){
      if (rnn_p->tau[i] > 1000){
	rnn_p->pb_num += 1;
      }
    }

    if (series_id >= 0 && series_id < runner->id) {
        copy_init_state(runner->rnn.rnn_s + runner->id, runner->rnn.rnn_s +
                series_id);
    } else {
        random_init_state(runner->rnn.rnn_s + runner->id);
    }
    
    MALLOC2(rnn_s_reg->assigned_pb, runner->id, rnn_p->pb_num);
    
    /*
    for (int s = 0; s < runner->id; s++){
      struct rnn_state *rnn_s_src = runner->rnn.rnn_s + s;
	for ( int i = 0; i < rnn_p->pb_num; i++){
	  rnn_s_reg->assigned_pb[s][i] = rnn_s_src->init_c_inter_state[ i + rnn_p->c_state_size - rnn_p->pb_num];
	}
    }
    */

    
    //for the without assigned pb case
    double tmp = 0;
    int count = 0;
    
    for (int i = 0; i < rnn_p->pb_num; i++){
      int point = 0;
      for (int s = 0; s < runner->id; s++){
	struct rnn_state *rnn_s_src = runner->rnn.rnn_s + s;
	tmp += rnn_s_src->init_c_inter_state[i + rnn_p->c_state_size - rnn_p->pb_num];
	count += 1;
	if (count ==3){
	  tmp = tmp/3;
	  for (int j = s; j >= point; j--){
	    rnn_s_reg->assigned_pb[j][i] = tmp;
	  }
	  //printf("%f     ", rnn_s_reg->assigned_pb[s][i]);
	  tmp = 0;
	  count = 0;
	  point = s+1;
	}
      }
      //printf("\n");
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

    //rnn_forward_backward_dynamics(rnn_s);
    //rnn_forward_dynamics(rnn_s);
    
    rnn_forward_dynamics_in_closed_loop(rnn_s, delay_length);
    

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
		int init_id, 
		int time_step,
        double *input,
        int reg_count,
        double rho_init,
        double momentum, 
	double gamma_bp,
	double gamma_top)
{
  /*
    struct rnn_state *rnn_s = runner->rnn.rnn_s + runner->id;
    struct rnn_parameters *rnn_p = rnn_s->rnn_p;


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

if (time_step < 350){
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num] = 1;
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num + 1] = 1;
    }      
    else if (time_step < 600){
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num] = 1;
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num + 1] = 1;
    }
    else if (time_step < 950){
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num] = 1;
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num + 1] = -1;
    }
    else if (time_step < 1200){
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num] = 1;
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num + 1] = -1;
    }

    rnn_fmap(rnn_s, runner->delay_length);

  */

  
    struct rnn_state *rnn_s = runner->rnn.rnn_s + runner->id;
    struct rnn_parameters *rnn_p = rnn_s->rnn_p;


    if (input != NULL) {
        memmove(rnn_s->in_state[rnn_s->length - 1], input, sizeof(double) *
                rnn_s->rnn_p->in_state_size);
        memmove(rnn_s->teach_state[rnn_s->length - runner->delay_length - 1],
                input, sizeof(double) * rnn_s->rnn_p->out_state_size);
	
	//teach_state[t] = input[t+d]
	//rnn_s->length = delay_length + windows_length
	
	if (time_step < rnn_s->length - 1) {
	  memmove(rnn_s->in_state[0], input, sizeof(double) *
		  rnn_s->rnn_p->in_state_size);
	}	
    }

    int tmp_length = rnn_s->length;
    rnn_s->length -= runner->delay_length;  //means equal to windows_length
    rho_init /= rnn_s->length * rnn_s->rnn_p->out_state_size;
    if (tmp_length - 2 < time_step) { // 20150909
      
    double error;
    error = rnn_get_error2(rnn_s);      
    error = error / (2 * rnn_s->length);
    // 2 is vision dimension

    if (error>0.02){
      printf("error");
      printf("%f    ",error);  
      printf("\n");
      for (int i = 0; i < reg_count; i++) {
	//rnn_forward_backward_dynamics(rnn_s);
	//rnn_forward_dynamics(rnn_s);
	rnn_forward_dynamics_in_closed_loop(rnn_s, runner->delay_length);
	rnn_set_likelihood2(rnn_s);
	rnn_backward_dynamics2(rnn_s);
        rnn_update_delta_init_c_inter_state2(rnn_s, momentum, gamma_bp, gamma_top, runner->id);
        rnn_update_init_c_inter_state(rnn_s, rho_init);
      }
     }
    }
    rnn_s->length = tmp_length;


    /*
    //for testing whether correct pb can generate correct patterns or not
    if (time_step < 330){
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num] = -0.248874;
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num + 1] = -0.575024;
    }      
    else if (time_step < 600){
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num] = 0.634308;
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num + 1] = 0.573374;
    }
    else if (time_step < 920){
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num] = 0.333232;
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num + 1] = -0.644006;
    }
    else if (time_step < 1200){
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num] = -0.696236;
      rnn_s->init_c_inter_state[rnn_p->c_state_size - rnn_p->pb_num + 1] = 0.490039;
    }
    */



    rnn_fmap(rnn_s, runner->delay_length);
    if (time_step < rnn_s->length - 1) {
      memmove(rnn_s->c_inter_state[rnn_s->length - 1], rnn_s->init_c_inter_state,
	      sizeof(double) * rnn_s->rnn_p->c_state_size);
      memmove(rnn_s->out_state[rnn_s->length - 1], rnn_s->out_state[0],
	      sizeof(double) * rnn_s->rnn_p->out_state_size);
      memmove(rnn_s->var_state[rnn_s->length - 1], rnn_s->var_state[0],
	      sizeof(double) * rnn_s->rnn_p->out_state_size);
    }
    
    if (time_step == rnn_s->length - 2) {
      memmove(rnn_s->init_c_inter_state, 
	      (runner->rnn.rnn_s + init_id)->init_c_inter_state,
	      sizeof(double) * rnn_s->rnn_p->c_state_size);
      memmove(rnn_s->init_c_state, 
	      (runner->rnn.rnn_s + init_id)->init_c_state,
	      sizeof(double) * rnn_s->rnn_p->c_state_size);
    }
  
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

