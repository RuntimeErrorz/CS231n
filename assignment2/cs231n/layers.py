from builtins import range
import numpy as np


def affine_forward(x, w, b):
    """Computes the forward pass for an affine (fully connected) layer.

    The input x has shape (N, d_1, ..., d_k) and contains a minibatch of N
    examples, where each example x[i] has shape (d_1, ..., d_k). We will
    reshape each input into a vector of dimension D = d_1 * ... * d_k, and
    then transform it to an output vector of dimension M.

    Inputs:
    - x: A numpy array containing input data, of shape (N, d_1, ..., d_k)
    - w: A numpy array of weights, of shape (D, M)
    - b: A numpy array of biases, of shape (M,)

    Returns a tuple of:
    - out: output, of shape (N, M)
    - cache: (x, w, b)
    """
    # (2(batches), 120(每个样本的总特征数)) dot (120, 3（类别数）) + (3,) = (2, 3)
    out = np.dot(x.reshape(x.shape[0], -1), w) + b
    return out, (x, w, b)


def affine_backward(dout, cache):
    """Computes the backward pass for an affine (fully connected) layer.

    Inputs:
    - dout: Upstream derivative, of shape (N, M)
    - cache: Tuple of:
      - x: Input data, of shape (N, d_1, ... d_k)
      - w: Weights, of shape (D, M)
      - b: Biases, of shape (M,)

    Returns a tuple of:
    - dx: Gradient with respect to x, of shape (N, d1, ..., d_k)
    - dw: Gradient with respect to w, of shape (D, M)
    - db: Gradient with respect to b, of shape (M,)
    """
    x, w, b = cache
    dx, dw, db = None, None, None
    dx = dout.dot(w.T).reshape(x.shape)  # (2, 3) * （3, 120） -> (2, 4, 5, 6)
    # (2, 4, 5, 6) -> (2, 120).T -> (120, 2) dot (2, 3) -> (120, 3)
    dw = x.reshape(x.shape[0], -1).T.dot(dout)
    db = np.sum(dout, axis=0)
    return dx, dw, db


def relu_forward(x):
    """Computes the forward pass for a layer of rectified linear units (ReLUs).

    Input:
    - x: Inputs, of any shape

    Returns a tuple of:
    - out: Output, of the same shape as x
    - cache: x
    """
    out = np.maximum(x, 0)
    cache = x
    return out, cache


def relu_backward(dout, cache):
    """Computes the backward pass for a layer of rectified linear units (ReLUs).

    Input:
    - dout: Upstream derivatives, of any shape
    - cache: Input x, of same shape as dout

    Returns:
    - dx: Gradient with respect to x
    """
    dx, x = None, cache
    dx = np.where(x > 0, dout, 0)
    return dx


def softmax_loss(x, y):
    """Computes the loss and gradient for softmax classification.

    Inputs:
    - x: Input data, of shape (N, C) where x[i, j] is the score for the jth
      class for the ith input.
    - y: Vector of labels, of shape (N,) where y[i] is the label for x[i] and
      0 <= y[i] < C

    Returns a tuple of:
    - loss: Scalar giving the loss
    - dx: Gradient of the loss with respect to x
    """
    loss, dx = None, None
    shifted_x = x - np.max(x, axis=1, keepdims=True)
    log_probs = shifted_x - \
        np.log(np.sum(np.exp(shifted_x), axis=1, keepdims=True))
    loss = -np.sum(log_probs[np.arange(x.shape[0]), y]) / x.shape[0]

    dx = np.exp(log_probs)
    dx[np.arange(x.shape[0]), y] -= 1
    dx /= x.shape[0]
    return loss, dx


def batchnorm_forward(x, gamma, beta, bn_param):
    """
    Input:
    - x: Data of shape (N, D)
    - gamma: Scale parameter of shape (D,)
    - beta: Shift paremeter of shape (D,)
    - bn_param: Dictionary with the following keys:
      - mode: 'train' or 'test'; required
      - eps: Constant for numeric stability
      - momentum: Constant for running mean / variance.
      - running_mean: Array of shape (D,) giving running mean of features
      - running_var Array of shape (D,) giving running variance of features

    Returns a tuple of:
    - out: of shape (N, D)
    - cache: A tuple of values needed in the backward pass
    """

    mode = bn_param["mode"]
    eps = bn_param.get("eps", 1e-5)
    momentum = bn_param.get("momentum", 0.9)
    layernorm = bn_param.get("layernorm", False)
    N, D = x.shape
    running_mean = bn_param.get("running_mean", np.zeros(D, dtype=x.dtype))
    running_var = bn_param.get("running_var", np.zeros(D, dtype=x.dtype))

    out, cache = None, None
    axis = 1 if layernorm else 0
    if mode == "train" or layernorm:
        x_mean = x.mean(axis=0)  # (D,) axis = 0 means 沿着column方向
        x_var = x.var(axis=0)
        x_hat = (x - x_mean) / np.sqrt(x_var + eps)
        out = gamma * x_hat + beta
        if not layernorm:
            running_mean = momentum * running_mean + (1 - momentum) * x_mean
            running_var = momentum * running_var + (1 - momentum) * x_var
        cache = x, x_mean, x_var, x_hat, gamma, eps, axis, bn_param
    elif mode == "test":
        out = gamma * ((x - running_mean) / np.sqrt(running_var + eps)) + beta
    else:
        raise ValueError('Invalid forward batchnorm mode "%s"' % mode)

    # Store the updated running means back into bn_param
    bn_param["running_mean"] = running_mean
    bn_param["running_var"] = running_var

    return out, cache


def batchnorm_backward(dout, cache):
    """Backward pass for batch normalization.

    Inputs:
    - dout: Upstream derivatives, of shape (N, D)
    - cache: Variable of intermediates from batchnorm_forward.

    Returns a tuple of:
    - dx: Gradient with respect to inputs x, of shape (N, D)
    - dgamma: Gradient with respect to scale parameter gamma, of shape (D,)
    - dbeta: Gradient with respect to shift parameter beta, of shape (D,)
    """
    x, x_mean, x_var, x_hat, gamma, eps, axis, _ = cache
    dbeta = np.sum(dout, axis=axis)
    dgamma = np.sum(dout * x_hat, axis=axis)

    dx_hat = dout * gamma

    dsigma_square = -0.5*np.sum(dx_hat*(x-x_mean),
                                axis=0) * (x_var+eps)**(-1.5)

    dmu = -np.sum(dx_hat / np.sqrt(x_var + eps), axis=0) - 2 * \
        dsigma_square*np.sum(x-x_mean, axis=0) / x.shape[0]

    dx = dx_hat / np.sqrt(x_var + eps) + dsigma_square * \
        2 * (x-x_mean) / x.shape[0] + dmu / x.shape[0]

    return dx, dgamma, dbeta


def batchnorm_backward_alt(dout, cache):
    """Alternative backward pass for batch normalization.

    For this implementation you should work out the derivatives for the batch
    normalizaton backward pass on paper and simplify as much as possible. You
    should be able to derive a simple expression for the backward pass.
    See the jupyter notebook for more hints.

    Note: This implementation should expect to receive the same cache variable
    as batchnorm_backward, but might not use all of the values in the cache.

    Inputs / outputs: Same as batchnorm_backward
    """
    dx, dgamma, dbeta = None, None, None
    x, x_mean, x_var, x_hat, gamma, eps, _, _ = cache

    N, D = x.shape

    dgamma = np.sum(dout * x_hat, axis=0, keepdims=True)
    dbeta = np.sum(dout, axis=0, keepdims=True)
    dx_gamma = dout*gamma

    x_m = x - x_mean
    ivar_sqrt = 1. / np.sqrt(x_var + eps)

    divar = np.sum(x_m * dx_gamma, axis=0, keepdims=True)
    dx_m1 = dx_gamma * ivar_sqrt

    dvar = -divar * ivar_sqrt**2
    dvar_sqrt = 0.5 * dvar * ivar_sqrt

    dsq = 1. / N * np.ones((N, D)) * dvar_sqrt

    dx_m2 = 2. * x_m * dsq

    dx_m = dx_m1 + dx_m2

    dmean = - 1. / N * np.sum(dx_m, axis=0, keepdims=True)

    dx = dx_m + dmean

    return dx, dgamma, dbeta


def layernorm_forward(x, gamma, beta, ln_param):

    ln_param['layernorm'] = True
    out, cache = batchnorm_forward(x.T, gamma.reshape(-1, 1),
                                   beta.reshape(-1, 1), ln_param)
    out = out.T
    '''
    x.T = (D, N)
    gamma.reshape(-1, 1) = (D, 1)
    beta.reshape(-1, 1) = (D, 1)
    '''
    return out, cache


def layernorm_backward(dout, cache):
    """Backward pass for layer normalization.

    For this implementation, you can heavily rely on the work you've done already
    for batch normalization.

    Inputs:
    - dout: Upstream derivatives, of shape (N, D)
    - cache: Variable of intermediates from layernorm_forward.

    Returns a tuple of:
    - dx: Gradient with respect to inputs x, of shape (N, D)
    - dgamma: Gradient with respect to scale parameter gamma, of shape (D,)
    - dbeta: Gradient with respect to shift parameter beta, of shape (D,)
    """
    dx, dgamma, dbeta = batchnorm_backward(dout.T, cache)
    return dx.T, dgamma, dbeta


def dropout_forward(x, dropout_param):
    p, mode = dropout_param["p"], dropout_param["mode"]
    if "seed" in dropout_param:
        np.random.seed(dropout_param["seed"])

    mask = None
    out = None
    if mode == "train":
        mask = (np.random.rand(*x.shape) < p) / p
        out = x * mask
    elif mode == "test":
        out = x

    cache = (dropout_param, mask)
    out = out.astype(x.dtype, copy=False)

    return out, cache


def dropout_backward(dout, cache):
    """Backward pass for inverted dropout.

    Inputs:
    - dout: Upstream derivatives, of any shape
    - cache: (dropout_param, mask) from dropout_forward.
    """
    dropout_param, mask = cache
    mode = dropout_param["mode"]

    dx = None
    if mode == "train":
        dx = mask * dout
    elif mode == "test":
        dx = dout
    return dx


def conv_forward_naive(x, w, b, conv_param):
    """A naive implementation of the forward pass for a convolutional layer.

    The input consists of N data points, each with C channels, height H and
    width W. We convolve each input with F different filters, where each filter
    spans all C channels and has height HH and width WW.

    Input:
    - x: Input data of shape (N, C, H, W)
    - w: Filter weights of shape (F, C, HH, WW)
    - b: Biases, of shape (F,)
    - conv_param: A dictionary with the following keys:
      - 'stride': The number of pixels between adjacent receptive fields in the
        horizontal and vertical directions.
      - 'pad': The number of pixels that will be used to zero-pad the input.

    During padding, 'pad' zeros should be placed symmetrically (i.e equally on both sides)
    along the height and width axes of the input. Be careful not to modfiy the original
    input x directly.

    Returns a tuple of:
    - out: Output data, of shape (N, F, H', W') where H' and W' are given by
      H' = 1 + (H + 2 * pad - HH) / stride
      W' = 1 + (W + 2 * pad - WW) / stride
    - cache: (x, w, b, conv_param)
    """
    stride, pad = conv_param['stride'], conv_param['pad']
    N, _, H, W = x.shape
    F, _, HH, WW = w.shape
    OUTH = 1 + (H + 2 * pad - HH) // stride
    OUTW = 1 + (W + 2 * pad - WW) // stride
    out = np.zeros((N, F, OUTH, OUTW))
    x_pad = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)), 'constant')
    for n in range(N):
        for f in range(F):
            for i in range(OUTH):
                for j in range(OUTW):
                    out[n, f, i, j] = (x_pad[n, :, i*stride:i*stride+HH,
                                             j * stride:j*stride+WW] * w[f]).sum() + b[f]
    cache = (x, w, b, conv_param)
    return out, cache


def conv_backward_naive(dout, cache):
    """
    A naive implementation of the backward pass for a convolutional layer.

    Inputs:
    - dout: Upstream derivatives.
    - cache: A tuple of (x, w, b, conv_param) as in conv_forward_naive

    Returns a tuple of:
    - dx: Gradient with respect to x
    - dw: Gradient with respect to w
    - db: Gradient with respect to b
    """
    x, w, b, conv_param = cache
    dx, dw, db = np.zeros_like(x), np.zeros_like(
        w), np.sum(dout, axis=(0, 2, 3))
    stride, pad = conv_param['stride'], conv_param['pad']
    x_pad = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)), 'constant')
    dx_pad = np.zeros_like(x_pad)
    N, C, H, W = x.shape
    F, C, HH, WW = w.shape
    OUTH = 1 + (H + 2 * pad - HH) // stride
    OUTW = 1 + (W + 2 * pad - WW) // stride
    for n in range(N):
        for f in range(F):
            for i in range(OUTH):
                for j in range(OUTW):
                    dx_pad[n, :, i*stride:i*stride+HH,
                           j * stride:j*stride+WW] += dout[n, f, i, j] * w[f]
                    dw[f] += dout[n, f, i, j] * x_pad[n, :,
                                                      i*stride:i+HH, j*stride:j*stride+WW]
    dx = dx_pad[:, :, pad:-pad, pad:-pad]
    return dx, dw, db


def max_pool_forward_naive(x, pool_param):
    """A naive implementation of the forward pass for a max-pooling layer.

    Inputs:
    - x: Input data, of shape (N, C, H, W)
    - pool_param: dictionary with the following keys:
      - 'pool_height': The height of each pooling region
      - 'pool_width': The width of each pooling region
      - 'stride': The distance between adjacent pooling regions

    No padding is necessary here, eg you can assume:
      - (H - pool_height) % stride == 0
      - (W - pool_width) % stride == 0

    Returns a tuple of:
    - out: Output data, of shape (N, C, H', W') where H' and W' are given by
      H' = 1 + (H - pool_height) / stride
      W' = 1 + (W - pool_width) / stride
    - cache: (x, pool_param)
    """
    N, C, H, W = x.shape
    pool_height, pool_width, stride = pool_param['pool_height'], pool_param['pool_width'], pool_param['stride']
    OUTH = 1 + (H - pool_height) // stride
    OUTW = 1 + (W - pool_width) // stride
    out = np.zeros((N, C, OUTH, OUTW))
    for n in range(N):
        for i in range(OUTH):
            for j in range(OUTW):
                out[n, :, i, j] = np.max(
                    x[n, :, i*stride:i*stride+pool_height, j*stride:j*stride+pool_width], axis=(1, 2))
    cache = (x, pool_param)
    return out, cache


def max_pool_backward_naive(dout, cache):
    """A naive implementation of the backward pass for a max-pooling layer.

    Inputs:
    - dout: Upstream derivatives
    - cache: A tuple of (x, pool_param) as in the forward pass.

    Returns:
    - dx: Gradient with respect to x
    """
    x, pool_param = cache
    N, C, H, W = x.shape
    pool_height, pool_width, stride = pool_param['pool_height'], pool_param['pool_width'], pool_param['stride']
    OUTH = 1 + (H - pool_height) // stride
    OUTW = 1 + (W - pool_width) // stride
    dx = np.zeros_like(x)
    for n in range(N):
        for c in range(C):
            for i in range(OUTH):
                for j in range(OUTW):
                    index = np.argmax(
                        x[n, c, i*stride:i*stride+pool_height, j*stride:j*stride+pool_width])
                    index1, index2 = np.unravel_index(
                        index, (pool_height, pool_width))
                    dx[n, c, i*stride:i*stride+pool_height, j*stride:j *
                        stride+pool_height][index1, index2] = dout[n, c, i, j]
    return dx


def spatial_batchnorm_forward(x, gamma, beta, bn_param):
    """Computes the forward pass for spatial batch normalization.

    Inputs:
    - x: Input data of shape (N, C, H, W)
    - gamma: Scale parameter, of shape (C,)
    - beta: Shift parameter, of shape (C,)
    - bn_param: Dictionary with the following keys:
      - mode: 'train' or 'test'; required
      - eps: Constant for numeric stability
      - momentum: Constant for running mean / variance. momentum=0 means that
        old information is discarded completely at every time step, while
        momentum=1 means that new information is never incorporated. The
        default of momentum=0.9 should work well in most situations.
      - running_mean: Array of shape (D,) giving running mean of features
      - running_var Array of shape (D,) giving running variance of features

    Returns a tuple of:
    - out: Output data, of shape (N, C, H, W)
    - cache: Values needed for the backward pass
    """
    N, C, H, W = x.shape
    # transpose to a channel-last notation (N, H, W, C) and then reshape it to
    # norm over N*H*W for each C
    # (N, C, H, W) -> (N, H, W, C) -> (N*H*W, C)
    x = x.transpose(0, 2, 3, 1).reshape(N*H*W, C)
    # axis = 0, so norm over N*H*W
    out, cache = batchnorm_forward(x, gamma, beta, bn_param)
    # transpose the output back to N, C, H, W
    out = out.reshape(N, H, W, C).transpose(0, 3, 1, 2)
    return out, cache


def spatial_batchnorm_backward(dout, cache):
    """Computes the backward pass for spatial batch normalization.

    Inputs:
    - dout: Upstream derivatives, of shape (N, C, H, W)
    - cache: Values from the forward pass

    Returns a tuple of:
    - dx: Gradient with respect to inputs, of shape (N, C, H, W)
    - dgamma: Gradient with respect to scale parameter, of shape (C,)
    - dbeta: Gradient with respect to shift parameter, of shape (C,)
    """
    N, C, H, W = dout.shape
    dout = dout.transpose(0, 2, 3, 1).reshape(N*H*W, C)
    dx, dgamma, dbeta = batchnorm_backward(dout, cache)
    dx = dx.reshape(N, H, W, C).transpose(0, 3, 1, 2)
    return dx, dgamma, dbeta


def spatial_groupnorm_forward(x, gamma, beta, G, gn_param):
    """
    Computes the forward pass for spatial group normalization.
    In contrast to layer normalization, group normalization splits each entry 
    in the data into G contiguous pieces, which it then normalizes independently.
    Per feature shifting and scaling are then applied to the data, in a manner identical to that of batch normalization and layer normalization.

    Inputs:
    - x: Input data of shape (N, C, H, W)
    - gamma: Scale parameter, of shape (1, C, 1, 1)
    - beta: Shift parameter, of shape (1, C, 1, 1)
    - G: Integer mumber of groups to split into, should be a divisor of C
    - gn_param: Dictionary with the following keys:
      - eps: Constant for numeric stability

    Returns a tuple of:
    - out: Output data, of shape (N, C, H, W)
    - cache: Values needed for the backward pass
    """
    out, cache = None, None
    eps = gn_param.get("eps", 1e-5)
    N, C, H, W = x.shape
    x_group = x.reshape(N, G, C//G, H, W)
    mean = np.mean(x_group, axis=(2, 3, 4), keepdims=True)
    var = np.var(x_group, axis=(2, 3, 4), keepdims=True)
    x_groupnorm = (x_group - mean) / np.sqrt(var + eps)  #
    x_hat = x_groupnorm.reshape(N, C, H, W)
    out = x_hat * gamma + beta
    cache = (x, x_hat, mean, var, gamma,  eps, G)
    return out, cache


def spatial_groupnorm_backward(dout, cache):
    """
    Computes the backward pass for spatial group normalization.

    Inputs:
    - dout: Upstream derivatives, of shape (N, C, H, W)
    - cache: Values from the forward pass

    Returns a tuple of:
    - dx: Gradient with respect to inputs, of shape (N, C, H, W)
    - dgamma: Gradient with respect to scale parameter, of shape (1, C, 1, 1)
    - dbeta: Gradient with respect to shift parameter, of shape (1, C, 1, 1)
    """
    x, x_hat, mean, var, gamma, eps, G = cache
    dgamma = np.sum(dout * x_hat, axis=(0, 2, 3), keepdims=True)
    dbeta = np.sum(dout, axis=(0, 2, 3), keepdims=True)

    N, C, H, W = x.shape
    x_trans = x.reshape(N, G, C // G, H, W)
    m = C // G * H * W
    dx_hat = (dout * gamma).reshape(N, G, C // G, H, W)
    dvar = np.sum(dx_hat * (x_trans - mean) * (-0.5) *
                  np.power((var + eps), -1.5), axis=(2, 3, 4), keepdims=True)
    dmean = np.sum(dx_hat * (-1) / np.sqrt(var + eps), axis=(2, 3, 4), keepdims=True) + \
        dvar * np.sum(-2 * (x_trans - mean), axis=(2, 3, 4), keepdims=True) / m
    dx = dx_hat / np.sqrt(var + eps) + dvar * 2 * \
        (x_trans - mean) / m + dmean / m
    dx = dx.reshape(N, C, H, W)

    return dx, dgamma, dbeta
