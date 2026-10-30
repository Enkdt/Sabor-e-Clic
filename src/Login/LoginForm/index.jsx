import { useState } from 'react';
import { LoginImg } from '../../Assets/LoginImg';
import { SignBtn } from '../../Assets/SignBtn';
import { NextBtn } from '../../Components/NextBtn';
import { LoginDivider } from '../LoginDivider';
import { Input } from '../../Components/Input';
import './LoginForm.css';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../authContext';
export const LoginForm=()=>{

    const navigate=useNavigate();
    const { authenticate } = useAuth();
    const [email,setEmail] = useState('');
    const [password,setPassword] = useState('');
    const [error,setError]=useState('');

    const loginLogic = async (e) => {
        e.preventDefault();
        setError('');

        try {
            await authenticate(email, password);
            navigate("/");
        } catch (error) {
            setError(error.message);
        }
    }

    const inputs=[
        {
            label:"E-mail",
            placeholder:"exemplo@email.com",
            type:"text",
            value: email,
            onChange: (e) => setEmail(e.target.value)
        },
        {
            label:"Senha",
            placeholder:"Insira a sua senha",
            type:"password",
            //Pra botar os valores como tiver do input
            value: password,
            onChange: (e) => setPassword(e.target.value)
        }
    ]

return (
    <div className="loginDiv">
        <LoginImg/>

        <div className="loginForm w-full max-w-[800px]">
            <form onSubmit={loginLogic}>
                <h1 className="loginTitle transition-all duration-500 ease text-[44px] md:text-[54px] lg:text-[64px]">Bem-Vindo de volta!</h1>

                {inputs.map((input) => (
                    <div key={input.label}>
                        <Input
                            label={input.label}
                            placeholder={input.placeholder}
                            type={input.type}
                            value={input.value}
                            onChange={input.onChange}
                            className={error ? "loginInput error" : "loginInput"}
                        />

                        <p style={{ opacity: error ? 1 : 0 }} className="loginError">
                            {error || "errorPlaceholder"}
                        </p>
                    </div>
                ))}
                <NextBtn text="Continuar"/>
            </form>

            <LoginDivider/>
            <NavLink to="/cadastro">
                <SignBtn text="Cadastrar-se"/>
            </NavLink>
        </div>
    </div>
);

}