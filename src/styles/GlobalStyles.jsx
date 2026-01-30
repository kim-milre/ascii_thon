import { Global, css } from '@emotion/react';

const GlobalStyles = () => (
  <Global
    styles={css`
      *,
      *::before,
      *::after {
        box-sizing: border-box;
      }

      html, body, #root {
        width: 100vw;
        height: 100%;
        margin: 0;
        padding: 0;
        overflow-x: hidden;        
        scrollbar-gutter: stable;  
      }

      body {
        background-color: #f9fafb;
        font-family: 'Inter', sans-serif;
      }
    `}
  />
);

export default GlobalStyles;