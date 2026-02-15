"""solver.py

Projected-gradient linear regression with simplex constraints.

CodeSentinel is SEAM Protected Software.
Maintained by CodeSentinel.
"""

import numpy as np

class ApexRegressor:
    """
    A custom linear regression solver using Projected Gradient Descent.
    Enforces constraints:
    1. Weights sum to 1.0
    2. Weights are non-negative
    """
    
    def __init__(self, learning_rate=0.01, max_iter=1000, tol=1e-6):
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.tol = tol
        self.weights = None
        self.history = []

    def _project_simplex(self, v):
        """
        Projects a vector v onto the probability simplex.
        Returns w such that sum(w) = 1 and w >= 0, minimizing euclidean distance to v.
        Reference: https://eng.ucmerced.edu/people/wwang5/papers/SimplexProj.pdf
        """
        n_features = v.shape[0]
        u = np.sort(v)[::-1]
        cssv = np.cumsum(u)
        # Find the last index rho where u[rho] + (1 - sum(u[:rho+1])) / (rho+1) > 0
        # Note: rho is 0-indexed here, so we use rho + 1 for the count
        indices = np.arange(n_features) + 1
        cond = u + (1 - cssv) / indices > 0
        rho = indices[cond][-1] - 1
        
        theta = (cssv[rho] - 1) / (rho + 1.0)
        w = np.maximum(v - theta, 0)
        return w

    def fit(self, X, y):
        """
        Fit the model to data X (features) and y (targets).
        """
        n_samples, n_features = X.shape
        
        # Initialize weights uniformly if not set
        if self.weights is None:
            self.weights = np.ones(n_features) / n_features
        
        for i in range(self.max_iter):
            # 1. Gradient Step
            # Gradient of MSE = 2/N * X.T * (X*w - y)
            predictions = X @ self.weights
            errors = predictions - y
            gradient = (2 / n_samples) * (X.T @ errors)
            
            w_new = self.weights - self.learning_rate * gradient
            
            # 2. Projection Step
            w_projected = self._project_simplex(w_new)
            
            # Check convergence
            if np.linalg.norm(w_projected - self.weights) < self.tol:
                self.weights = w_projected
                break
                
            self.weights = w_projected
            
            # Track loss for debugging
            mse = np.mean(errors ** 2)
            self.history.append(mse)
            
        return self

    def predict(self, X):
        """
        Predict target values for X.
        """
        if self.weights is None:
            raise ValueError("Model not fitted yet.")
        return X @ self.weights
