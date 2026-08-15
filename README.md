# AI Sentence Builder Booth

초등학생이 LLM의 핵심 원리인 **“다음 말 예측”**을 직접 체험할 수 있도록 만든 부스용 데모입니다.

학생이 시작 문장을 입력하면 로컬 LLM이 다음에 올 가능성이 높은 후보들을 계산하고, 후보를 워드클라우드 형태로 보여줍니다. 학생은 화면에서 마음에 드는 말을 클릭해 문장을 이어가며, 선택에 따라 다음 후보가 즉시 달라지는 과정을 볼 수 있습니다.

## 핵심 아이디어

LLM은 문장을 한 번에 완성해서 쓰는 것이 아니라, 앞에 나온 글을 보고 **다음에 올 토큰의 가능성**을 계산합니다.

이 데모에서는 그 가능성을 워드클라우드로 시각화합니다.

- 글자가 클수록 다음에 올 가능성이 높습니다.
- 후보 하나를 클릭하면 현재 문장 뒤에 붙습니다.
- 새 문장에 맞춰 다음 후보가 다시 계산됩니다.
- 같은 시작 문장이라도 어떤 후보를 고르느냐에 따라 이야기가 달라집니다.

## 부스 체험 흐름

1. 실행하면 AI 모델을 먼저 불러옵니다.
2. Tkinter 입력창에 시작 문장을 입력합니다.
3. Matplotlib 화면에 현재 문장과 다음 말 후보가 표시됩니다.
4. 워드클라우드에서 후보를 클릭해 문장을 이어갑니다.
5. `처음부터` 버튼을 누르면 새 시작 문장으로 다시 시작합니다.

## 화면 특징

- 한글 입력감을 위해 시작 문장 입력은 Tkinter 팝업으로 분리했습니다.
- 워드클라우드는 Matplotlib 화면 안에서 클릭할 수 있습니다.
- 나눔스퀘어라운드가 설치되어 있으면 우선 사용합니다.
- 폰트가 표현하지 못하는 한자, 이모지, 특수문자 후보는 화면에서 제외합니다.
- 부스 화면에서 잘 보이도록 큰 글자, 부드러운 파스텔 색상, 단순한 안내 문구를 사용했습니다.

## 기술 구성

- Python
- PyTorch
- Hugging Face Transformers
- Qwen/Qwen2.5-1.5B-Instruct
- optimum-quanto INT8 quantization
- Matplotlib
- WordCloud
- Tkinter

## 파일 구성

```text
llm_booth/
  app.py                 # 부스 데모 실행 파일
  requirements.txt       # Python 패키지 목록
  run.bat                # Windows 간편 실행 파일
  docs/
    llm_booth_poster.png # 부스 안내 포스터
    llm_booth_slides.pdf # 사전 설명용 슬라이드
```

## 설치

Python 3.10 이상을 권장합니다.

```powershell
pip install -r requirements.txt
```

처음 실행할 때는 Hugging Face에서 모델을 다운로드하므로 시간이 걸릴 수 있습니다.

## 실행

```powershell
python app.py
```

Windows에서는 `run.bat`을 더블클릭해도 됩니다.

```powershell
.\run.bat
```

## 폰트

권장 폰트는 **나눔스퀘어라운드**입니다.

앱은 다음 순서로 한글 폰트를 찾습니다.

1. NanumSquareRound
2. Noto Sans KR
3. Malgun Gothic
4. AppleGothic
5. NanumGothic

폰트가 없어도 실행은 가능하지만, 부스 화면 가독성을 위해 나눔스퀘어라운드 또는 Noto Sans KR 설치를 권장합니다.

## 참고 자료

`docs` 폴더에는 부스 운영에 함께 사용할 수 있는 자료가 들어 있습니다.

- `llm_booth_poster.png`: 부스 앞에 붙일 안내 포스터
- `llm_booth_slides.pdf`: 체험 전 간단 설명용 슬라이드

데모 영상은 YouTube에서 확인할 수 있습니다.

- [AI Sentence Builder Booth Demo](https://youtu.be/nUphGuYHM1w?si=XANKVCOQn4DglBdb)

## 주의사항

- 이 데모는 로컬 LLM을 사용하므로 CPU 환경에서는 느릴 수 있습니다.
- 모델 파일은 저장소에 포함하지 않습니다.
- `.venv`, Hugging Face 캐시, Python 캐시 파일은 GitHub에 올리지 않는 것을 권장합니다.
- `QuantoConfig(weights="int8")`를 사용해 메모리 사용량을 줄입니다.

