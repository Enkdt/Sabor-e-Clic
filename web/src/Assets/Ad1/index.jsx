import ad1 from './ad1.png';
import './Ad1.css'
export const Ad1=()=>{
    return(
        <section className='ad1'>
            <img src={ad1} alt="ad1" className='ad1img' />
            <div className='ad1txt transition-all duration-150 ease text-[24px] md:text-[40px] lg:text-[60px]'>Clica<br/>e<br/>Vem</div>
        </section>
    ) 
}