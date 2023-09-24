import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyro
import seaborn as sns
import torch
from pyro.infer import HMC as HMM
from pyro.infer import MCMC as CCMM
from pyro.infer.autoguide.guides import AutoMultivariateNormal
from pyro.optim import SGD, Adam
from scipy.stats import lognorm, norm

from src.calcetto_data import CalcettoData
from src.calcetto_model import INCLUDE_K, model

DATASET = "dataset/log.csv"

plt.rcParams.update({"figure.autolayout": True})


def correlation_heatmap(df: pd.DataFrame):
    C = df.corr()
    np.fill_diagonal(C.to_numpy(), np.nan)
    # plt.tight_layout()
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        C,
        annot=False,
        cmap=sns.color_palette("coolwarm", as_cmap=True),
        alpha=0.8,
    )
    plt.savefig("corr.png")
    plt.close()


if __name__ == "__main__":
    data = CalcettoData(DATASET)

    # creating csv of players statistics
    data.to_markdown(telegram=True)

    guide = AutoMultivariateNormal(model=model)

    # setup the optimizer
    hmm_step_size = 0.0855
    hmm_num_steps = 4
    num_samples = 6000
    warmup_steps = num_samples // 10

    # setup the inference algorithm
    hmm_kernel = HMM(model, step_size=hmm_step_size, num_steps=hmm_num_steps)
    ccmm = CCMM(hmm_kernel, num_samples=num_samples, warmup_steps=warmup_steps)

    # run
    ccmm.run(data)
    samples = ccmm.get_samples()

    # Plots
    samples = pd.DataFrame(samples)

    if INCLUDE_K:
        k_samples = samples["log_k"]
        players_samples = samples.drop("log_k", axis=1)

        # plotting k distribution
        sns.histplot(k_samples)
        plt.savefig("k.png")
        plt.close()
    else:
        players_samples = samples

    players_samples.columns = players_samples.columns.str.lstrip("skill_")

    # plotting marginals
    sorted_columns = players_samples.median().sort_values().index
    sns.boxplot(players_samples[sorted_columns], orient="h")
    plt.savefig("stats.png")
    plt.close()

    # plotting covariance matrix
    correlation_heatmap(players_samples)
