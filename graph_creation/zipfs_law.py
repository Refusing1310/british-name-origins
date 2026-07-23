from matplotlib import pyplot as plt
import pandas as pd
import powerlaw
def plot_power_law_fit(elements_df: pd.DataFrame): 
    """Plot the element frequencies against index to check if elements follow Zipf's law, and follow a power law distribution."""
    freq = elements_df["Frequency"].to_numpy()

    fit = powerlaw.Fit(freq, discrete=True, verbose=False)

    alpha = fit.alpha
    xmin = fit.xmin

    R, p = fit.distribution_compare("power_law", "lognormal")
    if p < 0.05:
        if R > 0:
            print("Power law is statistically preferred.")
        else:
            print("Lognormal is statistically preferred.")
    else:
        print("No significant difference between the models.")

    fig = plt.figure(figsize=(8, 6))

    fit.plot_ccdf(
        color="black",
        linewidth=2,
        label="Observed"
    )

    fit.power_law.plot_ccdf(
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Power law (α={alpha:.2f})"
    )

    plt.xlabel("Element frequency")
    plt.ylabel("CCDF")
    plt.title("Power-law fit of place-name element frequencies")
    plt.legend()
    plt.grid(True, which="both", alpha=0.3)

    plt.savefig("data/processed/power_law_fit.png", dpi=300, bbox_inches="tight")
    plt.close(fig) 