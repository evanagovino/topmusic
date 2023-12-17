import numpy as np

def normalize_weights(weights):
    weight_sum = np.sum(weights)
    if weight_sum > 0:
        return [i/weight_sum for i in weights]
    else:
        return [1/len(weights) for i in weights]
        