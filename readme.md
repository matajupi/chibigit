# Chibigit
1. プログラムの用途 \
Gitのようなバージョン管理を行うことができる。

2. データ構造及びアルゴリズム \
多いので細かい部分は省略。(gitの動作原理は参考文献を参照)

3. ヒントを得たもの \
参考文献からヒントを得て作成した。

4. 参考文献 
    - https://qiita.com/noshishi/items/60a6fe7c63097950911b

## やったこと
車輪の再発明が趣味なので、前々から作りたいと思っていたGitのパチもんを作った。gitのindexやcommitに関連する主要コマンドまで実装できた。
具体的には、参考文献で作成しているプログラムをPythonで再実装し、多階層のプロジェクトにも対応できるようにするなどの改良を施している。
実装が複雑そうなので、Chibigitはブランチ等の機能はサポートしない予定だ。

## 動作方法(Ubuntuで動作確認済み)
Chibigitが使いやすいようにシンボリックリンクを作ってPathを通しておく。
```bash
$ chmod 777 main.py
$ ln -s main.py chibi
$ cd ../
$ export PATH=$PATH:/home/~~~~/chibigit
```

Chibigitで管理したいディレクトリに移動して、Chibigitプロジェクトを初期化する。
```bash
$ chibi init
```

snapコマンドでプロジェクト内のすべてのファイルをindexに追加することができる。
```bash
$ chibi snap
```

ls-filesコマンドはindex上に追加されているファイル一覧を表示する。
```bash
$ chibi ls-files
```

特定のパターンのファイルをChibigitの管理から外したいときは、プロジェクトの最上位ディレクトリに.chibiignoreファイルを作成して書き込んでおく。
```bash
$ echo ".json" >> .chibiignore
```

commitコマンドでindex上に存在するファイルをコミットすることができる。
```bash
$ chibi commit -m "Initial commit !!"
```

checkoutやlogなどのコマンドは実装が間に合わなかったので、今後行う予定だ。

## Future works
内部objectのOOPによる構造化、cat-fileの実装、checkoutの実装、logの実装、etc...

