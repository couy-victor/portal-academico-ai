import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="pt-BR">
      <Head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="description" content="Portal Acadêmico AI - UNISAL" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
