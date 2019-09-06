"""This module contains all the methods to obtain information about the
model uncertainty.

"""
import numpy as np
import pandas as pd


class Uncertainty:
    def __init__(self, ml):
        # Save a reference to the model.
        self.ml = ml

    def prediction_interval(self, n=1000, alpha=0.05, **kwargs):
        """Method to calculate the prediction interval for the simulation.

        Returns
        -------
        data: Pandas.DataFrame

        Notes
        -----
        Now calculates a "naive" prediction interval based on the residuals.
        This should probably be changed to something that recognizes the
        autocorrelation in the residuals (e.g. block bootstrapping).

        """
        params = self.get_parameter_sample(n=n)
        res = {}

        for i, param in enumerate(params):
            res[i] = self.ml.residuals(parameters=param, **kwargs)
        res = pd.DataFrame(res)

        #res = self.ml.residuals()
        sim = self.ml.simulate()
        q = [alpha / 2, 1 - alpha / 2]

        data = pd.DataFrame(
            {str(q[0]): sim.add(res.quantile(q[0]).quantile(q[0])),
             str(q[1]): sim.add(res.quantile(q[1]).quantile(q[1]))})
        return data

    def confidence_interval(self, n=None, alpha=0.05, **kwargs):
        """Method to calculate the confidence interval for the simulation.

        Returns
        -------

        Notes
        -----
        The confidence interval shows the uncertainty in the simulation due
        to parameter uncertainty. In other words, there is a 95% probability
        that the true best-fit line for the observed data lies within the
        95% confidence interval.

        """
        return self.get_realizations(func=self.ml.simulate,
                                     n=n, alpha=alpha, **kwargs)

    def block_response(self, name, n=None, alpha=0.05, **kwargs):
        dt = self.ml.get_block_response(name=name).index.values
        return self.get_realizations(func=self.ml.get_block_response, n=n,
                                     alpha=alpha, name=name, dt=dt, **kwargs)

    def step_response(self, name, n=None, alpha=0.05, **kwargs):
        dt = self.ml.get_block_response(name=name).index.values
        return self.get_realizations(func=self.ml.get_step_response, n=n,
                                     alpha=alpha, name=name, dt=dt, **kwargs)

    def contribution(self, name, n=None, alpha=0.05, **kwargs):
        return self.get_realizations(func=self.ml.get_contribution, n=n,
                                     alpha=alpha, name=name, **kwargs)

    def get_realizations(self, func, n=None, alpha=0.05, name=None, **kwargs):
        """Internal method """
        if name:
            kwargs["name"] = name

        params = self.get_parameter_sample(n=n, name=name)
        data = {}

        for i, param in enumerate(params):
            data[i] = func(parameters=param, **kwargs)

        q = [alpha / 2, 1 - alpha / 2]
        return pd.DataFrame(data).quantile(q=q, axis=1).transpose()

    def get_parameter_sample(self, name=None, n=None):
        """Method to obtain a parameter sets used in monte carlo simulation.

        Parameters
        ----------
        n: int, optional
            Number of random samples drawn from the bivariate normal
            distribution.
        name: str, optional
            Name of the stressmodel or model component to obtain the
            parameters for.

        Returns
        -------
        ndarray
            Numpy array with N parameter samples.

        """
        par = self.ml.get_parameters(name=name)
        pcov = self.get_covariance_matrix(name=name)

        if n is None:
            n = 10 ** par.size

        return np.random.multivariate_normal(par, pcov, n)

    def get_covariance_matrix(self, name=None):
        """Internal method to obtain the covariance matrix from the model.

        Parameters
        ----------
        name: str, optional
            Name of the stressmodel or model component to obtain the
            parameters for.

        Returns
        -------
        pcov: pandas.DataFrame
            Pandas DataFrame with the covariances for the parameters.

        """
        if name:
            params = self.ml.parameters.loc[self.ml.parameters.loc[:,
                                            "name"] == name].index
        else:
            params = self.ml.parameters.index

        return self.ml.fit.pcov.loc[params, params]
