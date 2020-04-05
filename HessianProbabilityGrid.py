import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import probscale
import scipy.stats as stats
from scipy.optimize import curve_fit
from scipy.stats import pearson3

matplotlib.use("pgf")
plt.rcParams.update({
    "pgf.rcfonts":
    False,
    "pgf.preamble": [
        "\\usepackage{xeCJK}",
        "\\usepackage{amsmath}",
        "\\usepackage{siunitx}",
        "\\sisetup{detect-all}"
        "\\usepackage{unicode-math}",
        "\\setsansfont{FiraGO}"
        "\\setmathfont{Fira Math}"
        "\\setCJKsansfont{Source Han Sans CN}",
    ],
})


class Data:
    """
    # 水文数据类

    ## 构造函数参数
    
    + `arr`：水文数据
    """
    def __init__(self, arr):
        self.arr = arr
        self.n = len(arr)

    def figure(self, grid=True, logVert=False):
        """
        # 绘制图形
        
        ## 输入参数
        
        + `gird`：是否显示背景网格，默认为 `True`
        
        + `logVert`：纵坐标是否为对数坐标，默认为 `False`
        
        + `font`：标签字体，默认为更纱黑体 CL
        """
        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        # 创建「画板」与「画布」

        self.ax.set_xscale("prob")
        # 横坐标改为概率坐标

        self.ax.set_xlabel(r"频率 $P$（%）")
        self.ax.set_ylabel(r"流量 $Q$（\si{\cubic m/s}）")

        self.ax.grid(grid)
        # 背景网格

        if logVert:
            self.ax.set_yscale("log")

    def statParams(self, varSkew=False, output=True):
        """
        # 输出数据的统计参数
        
        ## 输入参数
        
        + `varSkew`：偏态系数计算算法选择，具体可参考 wiki「Skewness」词条
        
        + `output`：是否在控制台输出参数，默认为 True
        """
        self.expectation = np.mean(self.arr)
        # 期望
        self.modulusRatio = self.arr / self.expectation
        # 模比系数
        self.coeffOfVar = np.sqrt(
            np.sum((self.modulusRatio - 1)**2) / (self.n - 1))
        # 变差系数

        if not varSkew:
            self.coeffOfSkew = np.sum((self.modulusRatio - 1)**3) / (
                (self.n - 3) * self.coeffOfVar**3)
        else:
            self.coeffOfSkew = stats.skew(self.arr, bias=False)
        # 偏态系数
        if output:
            print("期望 EX 为 %.2f" % self.expectation)
            print("变差系数 Cv 为 %.4f" % self.coeffOfVar)
            print("偏态系数 Cs 为 %.4f" % self.coeffOfSkew)

    def empiScatter(self):
        """
        # 点绘经验概率点
        
        ## 输入参数
        
        + `method`：经验频率计算方法，可选值见下列表
        
            - `"expectation"`：数学期望公式，默认
            
            - `"chegdayev"`：切哥达耶夫公式
            
            - `"hessian"`：海森公式
        """
        self.sorted = np.sort(self.arr)[::-1]
        # 逆序排序输入数组

        self.empiProb = (np.arange(self.n) + 1) / (self.n + 1) * 100
        # 数学期望公式计算经验概率

        if self.empiProb[0] > 1:
            self.probLimLeft = 1
        else:
            self.probLimLeft = 10**(np.ceil(np.log10(self.empiProb[0])) - 1)
        self.probLimRight = 100 - self.probLimLeft

        self.ax.set_xlim(self.probLimLeft, self.probLimRight)
        # 画布坐标轴设置

        self.ax.scatter(self.empiProb,
                        self.sorted,
                        marker="o",
                        c="none",
                        edgecolors="k",
                        label="经验概率点")
        # 点绘经验概率

    def momentPlot(self):
        """
        # 绘制矩法估计参数理论概率曲线
        """
        x = np.linspace(self.probLimLeft, self.probLimRight, 1000)
        theoY = (pearson3.ppf(1 - x / 100, self.coeffOfSkew) * self.coeffOfVar
                 + 1) * self.expectation

        self.ax.plot(x, theoY, "--", lw=1, label="矩法估计参数概率曲线")
        # 绘制理论曲线

    def plotFitting(self, svRatio=0, EXFitting=True, output=True):
        """
        # 优化适线
        
        ## 输入参数

        + `svRatio`：倍比系数，即偏态系数 `Cs` 与 变差系数 `Cv` 之比。
        
            默认为 0，即关闭倍比系数功能。
        
            - 当 `svRatio` ≠ 0 时，Cs 不参与适线运算中，且 `Cs` = `svRatio` × `Cv`；

            - 当 `svRatio` = 0 时，Cs 正常参与适线运算。

        + `EXFitting`：适线时是否调整 EX，默认为 True

        + `output`：是否在控制台输出参数，默认为 True
        """

        if svRatio == 0:
            if EXFitting:
                p3 = lambda prob, ex, cv, cs: (pearson3.ppf(
                    1 - prob / 100, cs) * cv + 1) * ex

                [self.fitEX, self.fitCV, self.fitCS], pcov = curve_fit(
                    p3, self.empiProb, self.sorted,
                    [self.expectation, self.coeffOfVar, self.coeffOfSkew])

            else:
                p3 = lambda prob, cv, cs: (pearson3.ppf(1 - prob / 100, cs) *
                                           cv + 1) * self.expectation

                [self.fitCV, self.fitCS
                 ], pcov = curve_fit(p3, self.empiProb, self.sorted,
                                     [self.coeffOfVar, self.coeffOfSkew])

                self.fitEX = self.expectation

        else:
            if EXFitting:
                p3 = lambda prob, ex, cv: (pearson3.ppf(
                    1 - prob / 100, cv * svRatio) * cv + 1) * ex

                [self.fitEX, self.fitCV
                 ], pcov = curve_fit(p3, self.empiProb, self.sorted,
                                     [self.expectation, self.coeffOfVar])

            else:
                p3 = lambda prob, cv: (pearson3.ppf(
                    1 - prob / 100, cv * svRatio) * cv + 1) * self.expectation

                [self.fitCV], pcov = curve_fit(p3, self.empiProb, self.sorted,
                                               [self.coeffOfVar])

                self.fitEX = self.expectation

            self.fitCS = self.fitCV * svRatio

        if output:
            print("适线后")
            print("期望 EX 为 %.2f" % self.fitEX)
            print("变差系数 Cv 为 %.4f" % self.fitCV)
            print("偏态系数 Cs 为 %.4f" % self.fitCS)

    def fittedPlot(self):
        """
        # 绘制适线后的概率曲线
        
        """

        x = np.linspace(self.probLimLeft, self.probLimRight, 1000)
        theoY = (pearson3.ppf(1 - x / 100, self.fitCS) * self.fitCV +
                 1) * self.fitEX

        self.ax.plot(x, theoY, lw=2, label="适线后概率曲线")
        # 绘制理论曲线

    def prob2Value(self, prob):
        """
        # 由设计频率转换设计值
        
        ## 输入参数
        
        + `prob`：设计频率，单位百分数
        
        ## 输出参数
        
        + `value`：设计值
        """

        value = (pearson3.ppf(1 - prob / 100, self.fitCS) * self.fitCV +
                 1) * self.fitEX

        print("%.4f%% 的设计频率对应的设计值为 %.2f" % (prob, value))

        return value

    def value2Prob(self, value):
        """
        # 由设计值转换设计参数
        
        ## 输入参数
        
        + `value`：设计值
        
        ## 输出参数
        
        + `prob`：设计频率，单位百分数
        """
        prob = 100 - pearson3.cdf(
            (value / self.fitEX - 1) / self.fitCV, self.fitCS) * 100

        print("%.2f 的设计值对应的设计频率为 %.4f%%" % (value, prob))

        return prob


data = Data(
    np.array([
        538.3, 624.9, 663.2, 591.7, 557.2, 998, 641.5, 341.1, 964.2, 687.3,
        546.7, 509.9, 769.2, 615.5, 417.1, 789.3, 732.9, 1064.5, 606.7, 586.7,
        567.4, 587.7, 709, 883.5
    ]))
# 6.3 题的数据


def main():
    data.figure()
    data.statParams()
    data.empiScatter()
    data.momentPlot()
    data.plotFitting()
    data.fittedPlot()

    data.prob2Value(prob=10)
    data.value2Prob(value=936.37)

    data.ax.legend()

    plt.tight_layout(0.5)
    plt.savefig("fig.pdf")


if __name__ == "__main__":
    main()
