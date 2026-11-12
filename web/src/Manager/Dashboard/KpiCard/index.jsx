import './KpiCard.css'
export const KpiCard=({label,badge,value,note})=>{
    return(
        <div className='kpiCard'>
            <div className='kpiCardTop'>
                <p className='kpiCardLabel'>{label}</p>
                <span className='kpiCardBadge'>{badge}</span>
            </div>
            <p className='kpiCardValue'>{value}</p>
            <p className='kpiCardNote'>{note}</p>
        </div>
    )
}
