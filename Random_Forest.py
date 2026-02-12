#!/usr/bin/env python
# coding: utf-8



# Import necessary libraries
import numpy as np
from sklearn.ensemble import RandomForestClassifier


# Random Forest Classification
def ML_Model_RF(X_train, X_test, Y_train, Y_test, param1, param2, param3, param4):
    
    # Create and train a Random Forest Regression model
    model = RandomForestClassifier(n_estimators= 100, max_depth= 10, min_samples_leaf= 4, min_samples_split= 10, random_state= 42, class_weight= 'balanced')
    # model = RandomForestClassifier(n_estimators= param1, max_depth= param2, min_samples_leaf= param3, min_samples_split= param4, random_state= 42, class_weight= 'balanced')
    model.fit(X_train, Y_train)
    
    # Make predictions and evaluate the model
    Y_pred = model.predict(X_test)
    
    return model, Y_pred

