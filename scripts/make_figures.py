"""Publication figures derived only from saved results and explicit formulas."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, NullLocator

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'figures'
BLUE='#24598f'; TEAL='#178579'; ORANGE='#bf6b31'; RED='#b34949'; GRAY='#6b7280'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,
                     'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,
                     'grid.color':'#e6e9ed','grid.linewidth':.6,'axes.axisbelow':True,
                     'pdf.fonttype':42,'ps.fonttype':42,'savefig.bbox':'tight'})

def save(fig,name):
    fig.savefig(OUT/f'{name}.pdf',metadata={'Creator':'Matplotlib; reproducible source in scripts/make_figures.py'})
    fig.savefig(OUT/f'{name}.png',dpi=200)
    plt.close(fig)

def main():
    s=json.loads((ROOT/'results/summary.json').read_text())
    x=pd.read_csv(ROOT/'results/synthetic.csv');x['gain']=1-x.cer/x['count']
    fig,axes=plt.subplots(1,3,figsize=(7.1,2.4),sharey=True)
    k,r=8,4
    loads=[np.full(k,1/k),np.r_[np.zeros(r),5/8,np.full(3,1/8)],np.r_[np.zeros(r),np.full(4,1/4)]]
    for ax,load,title,color in zip(axes,loads,['Normal operation','Shared first backup','Exposure-balanced backup'],[BLUE,ORANGE,TEAL]):
        ax.bar(np.arange(1,9),load,color=color,width=.72)
        ax.set(xticks=[1,2,3,4,5,6,7,8],xlabel='Endpoint',title=title,ylim=(0,.72))
        ax.text(.5,.92,f'Concentration = {load@load:.3f}',transform=ax.transAxes,ha='center',fontsize=8)
        if title!='Normal operation':
            ax.axvspan(.5,4.5,color='#f0f0f0',zorder=0)
            ax.text(2.5,.12,'Unavailable',ha='center',fontsize=8,color=GRAY)
    axes[0].set_ylabel('Share of financial exposure')
    fig.tight_layout(w_pad=1.2);save(fig,'01-contingent-concentration')

    fig,axes=plt.subplots(1,2,figsize=(7.1,2.55))
    kval=np.arange(4,101,2);rval=kval//2
    common=(kval+rval*(rval+1))/kval**2;balanced=1/(kval-rval)
    axes[0].plot(kval,common,label='Common backup',color=ORANGE)
    axes[0].plot(kval,balanced,label='Balanced backup',color=TEAL)
    axes[0].plot(kval,1/kval,label='Normal',color=BLUE,linestyle='--')
    axes[0].set(xlabel='Initially active endpoints K',ylabel='Squared exposure concentration',title='Half the endpoints unavailable')
    axes[0].legend(frameon=False,fontsize=8)
    for corr,color in [(0,BLUE),(.3,TEAL),(.8,ORANGE)]:
        ratio=(corr+(1-corr)*common)/(corr+(1-corr)*balanced)
        axes[1].plot(kval,ratio,label=f'Common-error correlation {corr:g}',color=color)
    axes[1].set(xlabel='Initially active endpoints K',ylabel='Common / balanced risk',title='Common errors limit diversification')
    axes[1].legend(frameon=False,fontsize=7)
    fig.tight_layout(w_pad=2);save(fig,'02-analytic-scaling')

    fig,axes=plt.subplots(1,2,figsize=(7.1,2.75))
    sub=x[(x.feedback==.4)&(x.correlation==0)]
    vals=[sub[sub.outage_size==r].groupby('network').gain.mean().values*100 for r in [1,2]]
    bp=axes[0].boxplot(vals,tick_labels=['One endpoint','Two endpoints'],patch_artist=True,widths=.45)
    for b,c in zip(bp['boxes'],[BLUE,TEAL]):b.set(facecolor=c,alpha=.25)
    for i,v in enumerate(vals):
        jitter=np.random.default_rng(31+i).uniform(-.12,.12,len(v))
        axes[0].scatter(i+1+jitter,v,s=8,color=[BLUE,TEAL][i],alpha=.55)
    axes[0].set(ylabel='Risk reduction vs count balance (%)',title='Paired means over 60 networks')
    for r,color in [(1,BLUE),(2,TEAL)]:
        points=[z for z in s['synthetic'] if z['feedback']==.4 and z['outage_size']==r]
        c=np.array([z['correlation'] for z in points]);y=np.array([z['gain'] for z in points])*100
        axes[1].errorbar(c,y[:,0],yerr=[y[:,0]-y[:,1],y[:,2]-y[:,0]],marker='o',capsize=3,color=color,label=f'{r} unavailable')
    axes[1].set(xlabel='Cross-endpoint error correlation',ylabel='Risk reduction (%)',title='Correlation sensitivity',xticks=[0,.3,.8])
    axes[1].legend(frameon=False)
    fig.tight_layout(w_pad=2);save(fig,'03-network-results')

    fig,axes=plt.subplots(1,2,figsize=(7.1,2.65))
    rnd=pd.read_csv(ROOT/'results/rounding.csv')
    for col,label,color in [('independent','Independent random routing',ORANGE),('rounded','Conditional-expectation rounding',TEAL)]:
        grouped=rnd.assign(value=rnd[col]/rnd.fractional).groupby('n').value
        avg=grouped.mean();std=grouped.std()/np.sqrt(20)
        axes[0].errorbar(avg.index,avg.values,yerr=1.96*std.values,color=color,marker='o',capsize=3,label=label)
    axes[0].axhline(1,color=GRAY,linestyle='--',label='Fractional lower bound')
    axes[0].set(xscale='log',xlabel='Number of institutions',ylabel='Risk / fractional lower bound',title='Finite decisions create a material gap')
    axes[0].set_xticks([4,8,16,32,64],labels=['4','8','16','32','64'])
    axes[0].xaxis.set_minor_locator(NullLocator())
    axes[0].legend(frameon=False,fontsize=6.7)
    # Exact examples, not fitted data.
    n=np.arange(4,65)
    axes[1].plot(n,1+3/n,color=BLUE,label='Equal, aligned exposures')
    axes[1].plot(n,np.full(len(n),4.),color=RED,label='Orthogonal exposures')
    axes[1].set(xlabel='Number of institutions',ylabel='Random / fractional risk',title='K = 4: headcount alone is insufficient',ylim=(.9,4.3))
    axes[1].legend(frameon=False,fontsize=7)
    fig.tight_layout(w_pad=2);save(fig,'04-indivisible-routing')

    fig,axes=plt.subplots(1,2,figsize=(7.1,2.7),gridspec_kw={'width_ratios':[1,1.25]})
    api=json.loads((ROOT/'results/api-run.json').read_text());C=np.array(api['calibration_cosine_second_moment'])
    im=axes[0].imshow(C,vmin=.8,vmax=1,cmap='Blues')
    names=['4.1 nano','4.1 mini','4o mini','4.1']
    axes[0].set(xticks=range(4),yticks=range(4),xticklabels=names,yticklabels=names,title='Calibration error alignment')
    axes[0].tick_params(axis='x',rotation=35);axes[0].grid(False)
    for i in range(4):
        for j in range(4):axes[0].text(j,i,f'{C[i,j]:.2f}',ha='center',va='center',fontsize=8,color='white' if C[i,j]>.94 else 'black')
    labels=['CER','Diagonal moment','Equal variance','Ridge envelope','Common best*']
    methods=['cer','diagonal','equal','robust','common']
    for i,(m,label) in enumerate(zip(methods,labels)):
        z=next(v for v in s['api'] if v['method']==m and v['outage_size']==0)
        mean,lo,hi=np.array(z['gain'])*100
        axes[1].errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt='o',color=ORANGE if m=='common' else TEAL,capsize=3)
    axes[1].axvline(0,color=GRAY,linestyle='--',linewidth=.8)
    axes[1].set(yticks=range(5),yticklabels=labels,xlabel='Held-out risk reduction (%)',title='128 paired held-out tasks')
    axes[1].invert_yaxis()
    fig.tight_layout(w_pad=1.5);save(fig,'05-api-replay')

    tail=pd.read_csv(ROOT/'results/tail-checks.csv')
    fig,ax=plt.subplots(figsize=(5.8,2.5))
    sub=tail[tail.correlation==0]
    groups=['normal','student_t5'];positions=np.arange(2)
    for i,(method,color) in enumerate([('common',ORANGE),('count',BLUE),('cer',TEAL)]):
        values=[sub[(sub.distribution==d)&(sub.method==method)].absolute_es975.iloc[0] for d in groups]
        ax.bar(positions+(i-1)*.23,values,width=.21,label=method,color=color)
    ax.set(xticks=positions,xticklabels=['Gaussian shocks','Student t (5 df)'],ylabel='Absolute-displacement ES97.5',title='Secondary tail check: one declared network')
    ax.legend(frameon=False,ncol=3)
    fig.tight_layout();save(fig,'06-tail-check')

if __name__=='__main__':main()
