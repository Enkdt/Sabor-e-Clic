import './ChartCard.css'
export const ChartCard=({title,badge,subtitle,scale,max,bars})=>{
    return(
        <section className='chartCard'>
            <div className='chartCardTop'>
                <h2>{title}</h2>
                <span className='chartCardBadge'>{badge}</span>
            </div>
            <p className='chartCardSubtitle'>{subtitle}</p>

            <div className='chartCardPlot'>
                <ul className='chartCardScale'>
                    {scale.map((tick)=>(
                        <li key={tick}>{tick}</li>
                    ))}
                </ul>
                <div className='chartCardBars'>
                    {bars.map((bar)=>(
                        <div key={bar.label} className='chartCardBar' style={{height:`${(bar.value/max)*100}%`}}></div>
                    ))}
                </div>
                <ul className='chartCardLabels'>
                    {bars.map((bar)=>(
                        <li key={bar.label}>{bar.label}</li>
                    ))}
                </ul>
            </div>
        </section>
    )
}
