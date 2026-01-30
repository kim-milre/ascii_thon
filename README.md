<<<<<<< HEAD
1. 가상환경 활성화
   - mac : ``` source venv/bin/activate```
    - window : ```venv\Scripts\activate```
   

2. 필요한 패키지 설치
    - ```pip install -r requirements.txt```
    - 새 패키지 설치가 필요하면 : ```pip install fastapi uvicorn spacy aiohttp```
  
 
3. FastAPI 서버 실행
    - ```uvicorn app.main:app --reload --host 0.0.0.0 --port 10000```
  
 
4. 실행 확인
   ```
      INFO: Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
      INFO: Application startup complete.
      ```
=======
# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
>>>>>>> 889efcfab551d573e330710c93b1dd499f8f91b2
