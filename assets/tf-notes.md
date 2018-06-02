


## gradient clipping

  - tf.clip_by_value

  - tf.clip_by_norm

  - tf.clip_by_average_norm

  - tf.clip_by_global_norm

  global norm is calculated, clip_norm is specified, 
  t_list[i] * clip_norm / max(global_norm, clip_norm)
  
  tf-doc says this is the correct way to do gradient clipping.

  - tf.global_norm

