


## gradient clipping

  - tf.clip_by_value
  
  min,max clipping

  - tf.clip_by_norm
  
  same as clip_by_global_norm but different ways calculating global_norm.
  
  
  t * clip_norm / l2norm(t)
  
  normalize t so that its l2-norm is no greater then given clip_norm.

  - tf.clip_by_average_norm

  - tf.clip_by_global_norm

  global norm is calculated, clip_norm is specified, 
  
  t_list[i] * clip_norm / max(global_norm, clip_norm)
  
  global_norm = sqrt(sum([l2norm(t)**2 for t in t_list]))
  
  tf-doc says this is the correct way to do gradient clipping.

  - tf.global_norm

