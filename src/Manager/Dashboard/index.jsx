import { CaretDownIcon } from '@phosphor-icons/react'
import { dashboardPeriod, dashboardKpis, salesChart, revenueChart } from '../../data/dashboardData'
import { Header } from '../../Components/Header'
import { KpiCard } from './KpiCard'
import { ChartCard } from './ChartCard'
import './Dashboard.css'
export const Dashboard=()=>{

    const filters=[
        { label: 'Período', options: ['Últimos 30 dias', 'Últimos 7 dias', 'Últimos 90 dias'] },
        { label: 'Região', options: ['Todas as regiões', 'Zona Sul', 'Zona Norte', 'Centro'] },
        { label: 'Categoria', options: ['Todas as categorias', 'Pratos', 'Sobremesas', 'Bebidas'] }
    ]

    return(
        <main className='dashboardPage'>
            <Header/>
            <div className='dashboardContent max-w-[1180px] mx-auto px-4'>
                <p className='dashboardEyebrow'>Painel administrativo</p>

                <div className='dashboardTop flex flex-col gap-4 md:flex-row md:items-end md:justify-between'>
                    <div>
                        <h1 className='text-[32px] md:text-[40px]'>Dashboard analítico</h1>
                        <p className='dashboardSubtitle'>Acompanhe vendas e desempenho dos restaurantes.</p>
                    </div>
                    <span className='dashboardPeriod'>{`Período: ${dashboardPeriod}`}</span>
                </div>

                <div className='dashboardFilters flex flex-col gap-3 sm:flex-row sm:flex-wrap'>
                    {filters.map((filter)=>(
                        <div key={filter.label} className='dashboardSelect'>
                            <select aria-label={filter.label}>
                                {filter.options.map((option)=>(
                                    <option key={option}>{option}</option>
                                ))}
                            </select>
                            <CaretDownIcon className='dashboardSelectIcon'/>
                        </div>
                    ))}
                    <button type='button' className='dashboardExport'>Exportar relatório</button>
                </div>

                <div className='dashboardKpis grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4'>
                    {dashboardKpis.map((kpi)=>(
                        <KpiCard key={kpi.id} label={kpi.label} badge={kpi.badge} value={kpi.value} note={kpi.note}/>
                    ))}
                </div>

                <div className='dashboardCharts grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4'>
                    <ChartCard {...salesChart}/>
                    <ChartCard {...revenueChart}/>
                </div>
            </div>
        </main>
    )
}
