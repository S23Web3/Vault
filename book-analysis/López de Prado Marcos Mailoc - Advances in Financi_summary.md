# Analysis: López de Prado, Marcos Mailoc - Advances in Financial Machine Learnin.epub

**Rating**: 10/10

**Size**: 13.1 MB | **Chapters**: 27

**Files**: [[López de Prado Marcos Mailoc - Advances in Financi_analysis.json]] (JSON data) | [[MASTER_SUMMARY]] (all books)

**Source**: `C:\Users\User\Downloads\López de Prado, Marcos Mailoc - Advances in Financial Machine Learnin.epub`

---

## Summary

- Trading concepts: 74
- ML concepts: 69
- Code: 23/27
- Formulas: 4/27

## Top Concepts

### Trading:
- **backtesting**: 469 mentions
- **psychology**: 130 mentions
- **metrics**: 130 mentions
- **risk**: 21 mentions
- **entries**: 17 mentions

### ML:
- **validation**: 235 mentions
- **metrics**: 234 mentions
- **supervised**: 74 mentions
- **features**: 67 mentions
- **models**: 46 mentions

---

## Chapters

### 1. Chapter

**Trading:**
- backtesting: 1
- psychology: 1

**Key Quotes:**
> The book blends the latest technological developments in ML with critical life lessons learned from the author's decades of financial experience in le...

> This book is an essential read for both practitioners and technologists working on solutions for the investment community...

> López de Prado's Advances in Financial Machine Learning is essential for readers who want to be ahead of the technology rather than being replaced by ...


### 2. Chapter


**ML:**
- metrics: 1

### 3. Chapter 1 Financial Machine Learning as a Distinct Subject

**Trading:**
- backtesting: 16
- psychology: 2

**ML:**
- supervised: 1
- features: 5
- models: 1
- validation: 14
- metrics: 5

**Key Quotes:**
> 2 Essential Types of Financial Data
2...


### 4. Chapter


### 5. CHAPTER 1 Financial Machine Learning as a Distinct Subject

**Trading:**
- risk: 1
- backtesting: 49
- metrics: 3
- psychology: 18

**ML:**
- supervised: 5
- features: 4
- models: 4
- validation: 19
- metrics: 5

**Key Quotes:**
> In my experience, there is one critical mistake that underlies all those failures...

> Those times are long gone, and today prospectors must deploy complex industrial methods to extract microscopic bullion particles out of tons of earth...

> They must develop the data handlers needed to understand the context in which that data arises...


### 6. CHAPTER 2 Financial Data Structures

**Trading:**
- entries: 4
- backtesting: 1
- psychology: 10

**ML:**
- metrics: 2

**Key Quotes:**
> 2 Essential Types of Financial Data
Financial data comes in many shapes and forms...

> 1 shows the four essential types of financial data, ordered from left to right in terms of increasing diversity...

> 1 The Four Essential Types of Financial Data




Fundamental Data
Market Data
Analytics
Alternative Data





Assets
Liabilities
Sales
Costs/earnings
...


### 7. CHAPTER 3 Labeling

**Trading:**
- entries: 3
- exits: 2
- backtesting: 1
- psychology: 11

**ML:**
- supervised: 8
- features: 1
- models: 19
- validation: 1
- metrics: 24

**Key Quotes:**
> But even these two improvements miss a key flaw of the fixed-time horizon method: the path followed by prices...

> In order to label an observation, we must take into account the entire path spanning [ti, 0, ti, 0 + h], where h defines the vertical barrier (the exp...

> Learning the side implies that either there are no horizontal barriers or that the horizontal barriers must be symmetric...


### 8. CHAPTER 4 Sample Weights

**Trading:**
- psychology: 4

**ML:**
- supervised: 3
- models: 4
- validation: 5
- metrics: 9

**Key Quotes:**
> We must allow ti, 1 > ti + 1, 0, which brings us back to the problem of overlapping outcomes described earlier...

> 2 Estimating the average uniqueness of a label




Note that we are making use again of the function mpPandasObj, which speeds up calculations via mul...

> For example, in the case of a random forest, all trees in the forest will essentially be very similar copies of a single overfit decision tree...


### 9. CHAPTER 5 Fractionally Differentiated Features

**Trading:**
- psychology: 1

**ML:**
- supervised: 2

**Key Quotes:**
> Note that , for n a positive integer...

> At a 95% confidence level, the test's critical value is –2...


### 10. CHAPTER 6 Ensemble Methods

**Trading:**
- backtesting: 11
- psychology: 10

**ML:**
- features: 1
- models: 4
- validation: 15
- metrics: 22

**Key Quotes:**
> When bias is high, the ML algorithm has failed to recognize important relations between features and outcomes...

> The key difference with bagging is that random forests incorporate a second level of randomness: When optimizing each node split, only a random subsam...

> Like bagging, RF reduces forecasts’ variance without overfitting (remember, as long as )...


### 11. CHAPTER 7 Cross-Validation in Finance

**Trading:**
- backtesting: 8
- psychology: 4

**ML:**
- supervised: 1
- models: 2
- validation: 34
- metrics: 3

**Key Quotes:**
> For leakage to take place, it must occur that (Xi, Yi) ≈ (Xj, Yj), and it does not suffice that Xi ≈ Xj or even Yi ≈ Yj...

> The test set is surrounded by two train sets, generating two overlaps that must be purged to prevent leakage...

> 5 Bugs in Sklearn's Cross-Validation
You would think that something as critical as cross-validation would be perfectly implemented in one of the most ...


### 12. CHAPTER 8 Feature Importance

**Trading:**
- entries: 1
- backtesting: 19
- psychology: 7

**ML:**
- supervised: 5
- features: 40
- models: 1
- validation: 10
- metrics: 48

**Key Quotes:**
> How to backtest properly is not the subject of this chapter; we will address that extremely important topic in Chapters 11–15...

> The goal of this chapter is to explain one of the analyses that must be performed before any backtest is carried out...

> Once we have found what features are important, we can learn more by conducting a number of experiments...


### 13. CHAPTER 9 Hyper-Parameter Tuning with Cross-Validation

**Trading:**
- risk: 1
- backtesting: 13
- metrics: 5
- psychology: 1

**ML:**
- supervised: 1
- models: 1
- validation: 10
- metrics: 21

**Key Quotes:**
> 1 Motivation
Hyper-parameter tuning is an essential step in fitting an ML algorithm...

> Note that a relabeling of cases has no impact on ‘accuracy’ or ‘neg_log_loss’, however it will have an impact on ‘f1’...

> Instead, it expects a fit_params keyworded argument...


### 14. CHAPTER 10 Bet Sizing

**Trading:**
- entries: 2
- risk: 5

**ML:**
- supervised: 4
- models: 1
- metrics: 3

**Key Quotes:**
> Note that for a real-valued price divergence x, − 1 < m[ω, x] < 1, the integer value  is bounded...


### 15. CHAPTER 11 The Dangers of Backtesting

**Trading:**
- risk: 1
- backtesting: 103
- metrics: 11
- psychology: 10

**ML:**
- features: 3
- validation: 27
- metrics: 4

**Key Quotes:**
> 1 Motivation
Backtesting is one of the most essential, and yet least understood, techniques in the quant arsenal...

> Even if some features are very important, it does not mean that they can be monetized through an investment strategy...

> Critically, feature importance is derived ex-ante, before the historical performance is simulated...


### 16. CHAPTER 12 Backtesting through Cross-Validation

**Trading:**
- risk: 1
- backtesting: 69
- metrics: 27
- psychology: 6

**ML:**
- validation: 25
- metrics: 1

**Key Quotes:**
> To be accurate and representative, each backtest must be customized to evaluate the assumptions of a particular strategy...

> WF enjoys two key advantages: (1) WF has a clear historical interpretation...

> Extreme care must be taken to avoid leaking testing information into the training set...


### 17. CHAPTER 13 Backtesting on Synthetic Data

**Trading:**
- entries: 1
- exits: 2
- risk: 1
- backtesting: 40
- metrics: 25
- psychology: 6

**ML:**
- validation: 16
- metrics: 1

**Key Quotes:**
> Trading rules provide the algorithm that must be followed to enter and exit a position...

> An important clarification is that we are interested in the exit corridor conditions that maximize performance...

> This is essentially the same definition we used in chapter 11 to derive PBO...


### 18. CHAPTER 14 Backtest Statistics

**Trading:**
- risk: 7
- backtesting: 25
- metrics: 25
- psychology: 4

**ML:**
- supervised: 6
- validation: 4
- metrics: 34

**Key Quotes:**
> If leverage takes place, costs must be assigned to it...

> When the correlation is significantly positive or negative, the strategy is essentially holding or short-selling the investment universe, without addi...

> Some important measurements of this include:
Broker fees per turnover: These are the fees paid to the broker for turning the portfolio over, including...


### 19. CHAPTER 15 Understanding Strategy Risk

**Trading:**
- backtesting: 2
- metrics: 18
- psychology: 2

**ML:**
- validation: 1
- metrics: 16

**Key Quotes:**
> 5, and the key to a successful business is to increase n...

> That is the critical difference we wish to establish with this chapter: Strategy risk should not be confused with portfolio risk...

> In order to be deployed, the strategy developer must find a way to reduce...


### 20. CHAPTER 16 Machine Learning Asset Allocation

**Trading:**
- entries: 1
- backtesting: 42
- metrics: 2
- psychology: 6

**ML:**
- supervised: 2
- models: 1
- validation: 2
- metrics: 3

**Key Quotes:**
> 1 HRP portfolios address three major concerns of quadratic optimizers in general and Markowitz's Critical Line Algorithm (CLA) in particular: instabil...

> On a daily basis, investment managers must build portfolios that incorporate their views and forecasts on risks and returns...

> Before earning his PhD in 1954, Markowitz left academia to work for the RAND Corporation, where he developed the Critical Line Algorithm...


### 21. CHAPTER 17 Structural Breaks

**Trading:**
- exits: 1
- psychology: 3

**ML:**
- supervised: 13

**Key Quotes:**
> The time-dependent critical value for the one-sided test is




These authors derived via Monte Carlo that b0...

> 1 Chow-Type Dickey-Fuller Test
A family of explosiveness tests was inspired by the work of Gregory Chow, starting with Chow [1960]...

> As Breitung [2014] explains, we should leave out some of the possible τ* at the beginning and end of the sample, to ensure that either regime is fitte...


### 22. CHAPTER 18 Entropy Features

**Trading:**
- entries: 1
- exits: 1
- backtesting: 5
- psychology: 3

**ML:**
- metrics: 1

**Key Quotes:**
> In other words, index i must be at the center of the window...

> This is important in order to guarantee that both matching strings are of the same length...

> A second caveat is that, because the window for matching must be symmetric (same length for the dictionary as for the substring being matched), the la...


### 23. CHAPTER 19 Microstructural Features

**Trading:**
- entries: 2
- exits: 1
- risk: 1
- backtesting: 1
- psychology: 2

**ML:**
- supervised: 8
- metrics: 4

**Key Quotes:**
> That makes microstructural data one of the most important ingredients for building predictive ML features...

> Essentially, it illustrated that market makers were sellers of the option to be adversely selected by informed traders, and the bid-ask spread is the ...

> 1 Implementation of the Corwin-Schultz algorithm




Note that volatility does not appear in the final Corwin-Schultz equations...


### 24. CHAPTER 20 Multiprocessing and Vectorization


**Key Quotes:**
> 1 Motivation
Multiprocessing is essential to ML...

> Then, r1 must satisfy the condition...

> Then, r2 must satisfy the condition...


### 25. CHAPTER 21 Brute Force and Quantum Computers

**Trading:**
- backtesting: 14
- metrics: 1

**Key Quotes:**
> This problem is particularly relevant to large asset managers, as the costs from excessive turnover and implementation shortfall may critically erode ...

> Note that non-continuous transaction costs are embedded in r...

> For example, if K = 6 and N = 3, partitions (1, 2, 3) and (3, 2, 1) must be treated as different (obviously (2, 2, 2) does not need to be permutated)...


### 26. CHAPTER 22 High-Performance Computational Intelligence and Forecasting Technologies

**Trading:**
- entries: 2
- psychology: 4

**ML:**
- supervised: 7
- metrics: 1

**Key Quotes:**
> The following sections explain the key features of HPC systems, introduce a few special tools used on these systems, and provide examples of streaming...

> A key aspect of financial big data is that it consists of mostly time series...

> The HPC tools have some critical advantages that should be useful in a variety of business applications...


### 27. Chapter

**Trading:**
- risk: 3
- backtesting: 49
- metrics: 13
- psychology: 15

**ML:**
- supervised: 8
- features: 13
- models: 8
- validation: 52
- metrics: 26

**Key Quotes:**
> See also Risk-based asset allocation approaches
tree clustering approaches to

Attribution
Augmented Dickey-Fuller (ADF) test...


