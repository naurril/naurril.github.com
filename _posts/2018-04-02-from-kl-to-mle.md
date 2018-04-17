---
layout: post
title: "From KL to MLE"
date: 2018-04-02
categories: howtos
commentIssueId: 1
---

{% include mathjs %}

MIT的课程 [18.650 statistics for applications](http://ocw.mit.edu/18-650F16)
在Lecture 4 讲MLE的时候，和一般书本上来就给出MLE公式的方法不同，这里使用Max variant distance -> KLdivergence ->MLE的方式，初看到这个过程，内心感觉还是比较有意思的，简单记录如下

假设我们要估算某个分布P的参数$$\theta^*$$，记为$$\hat{\theta}$$,我们希望分布$$P_\theta^*$$和$$P_\hat{\theta}$$越接近越好。
怎么衡量呢，使用total variant distance 

$$TV(P_\theta^*, P_\hat{\theta}) = \max_A{|P_{\theta^*}(A) - P_\hat{\theta}(A)|}$$ 

其中A表示某个事件。然后我们的策略是构造一个Esitmator $$\hat{TV}(P_\theta, P_{\theta^*})$$, 求使得它最小的$$\theta$$, 即$$\arg\min_\theta [\hat{TV}(P_\theta, P_{\theta^*})]$$

那么问题在哪里呢，我们不知道怎么构造这个表达式，$\theta^*$我们不知道，而且A的取值空间那么大，也不知道该怎么算。
于是我们用KL divergence, 虽然KL不是一个距离，而且$KL(P,Q) \neq KL(Q,P)$，但是当KL(P,Q)=0时，P=Q。
于是我们的Estimator变成了求KL的最小值对应的$$\theta$$, $$\arg\min_\theta[KL(P_{\theta^*}, P_\theta)]$$

代入KL的公式，

$$
KL(P_{\theta^*}, P_\theta) = E_{\theta^*} [\log{P_{\theta^*}(x) \over P_{\theta}(x)} ] = E_{\theta^*}[\log{P_{\theta^*}(x) ] - E_{\theta^*}[\log P_{\theta}(x)}]
$$

第一项是个常量, 第二项的是个期望值，我们可以从数据估算！

$$ KL(P_{\theta^*}, P_\theta)  \approx  Constant -  {1 \over n} \sum_{i=1}^N \log P_{\theta}(x_i)$$

这样我们求第2项的最大值不就行了。

$$
\arg\min_\theta \hat{KL}(P_{\theta^*}, P_\theta)  = \arg\max_\theta \sum_{i=1}^N \log P_{\theta}(x_i) =  \arg\max_\theta \prod_{i=1}^N P_{\theta}(x_i)
$$

这不就是MLE了吗！

由于KL散度展开后第一项是信息熵，不变，第2项是交叉熵([cross entropy](https://en.wikipedia.org/wiki/Cross_entropy))，所以其实我们是最小化两个分布的交叉熵。

注: 最后一步: $$\arg\max (\log a+\log b) = \arg\max \log ab = \arg\max ab$$

