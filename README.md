# DataBase

## 구현한 내용에 대한 설명

Lark 파일의 경우 이미 주어진 terminal이나 Select, Create SQL에 해당하는 rule 외에 insert, drop, explain, describe, desc, delete, show, update, exit에 해당하는 rule들을 추가하였습니다. 또 변경 사항에 맞게 기존의 ‘query’ rule에 새로 생성한 rule들을 추가하고, command: query_list | EXIT “;”를 command: query_list로 바꾸어 주었습니다.

Run.py에서는 lark 파일에서 문법을 읽어와 생성한 파서로 입력된 쿼리를 파싱하고, 파싱한 쿼리에 대해서는 transformer 클래스를 통해 쿼리에 맞는 output을 출력할 수 있도록 하였습니다. Output을 출력할 때는 항상 프롬프트가 띄워져야 하므로 커스텀 print 함수를 사용하였습니다.

## 알고리즘에 대한 설명

프로세스가 끝나는 조건은 ‘exit;’ 쿼리가 ‘처리될’ 때이므로 우선 계속 바깥 루프를 돌며 쿼리(들)의 입력과 입력된 쿼리(들)에 대한 처리를 반복합니다. inner loop가 종료되면(이번 턴의 입력이 종료되면) transformer 클래스의 메소드들을 통해 각 쿼리에 대한 output을 프린트하고 exit 쿼리가 detect된 경우 프로세스를 종료할 수 있도록 하였습니다. 이번 턴에 들어온 쿼리가 몇 개인지, 잘못된 쿼리가 포함되어 있는지는 실제로 쿼리 입력이 완료되기 전까지 알 수 없고 쿼리가 여러 줄로 나뉘어 들어올 수도 때문에 엔터를 쳤을 때 input의 마지막 character가 ‘;’가 될 때까지 inner loop를 돌게 됩니다. 다만 ‘;’ 전후의 whitespace는 고려하지 않으므로 input을 strip하여 공백을 제거한 후, ‘;’으로 끝난 경우 inner loop의 입력이 종료되었다고 간주하였습니다. 또 여러 줄로 나뉘어 들어오는 경우 newline이 사라지게 되기 때문에 각 줄의 끝에 space를 append해 주었습니다.

양쪽 공백이 제거된 입력 string을 ‘;’로 split해주면 list의 마지막 요소는 empty string이므로 무시하고, 나머지 요소들은 각각 끝에 ‘;’을 붙여 하나씩 파싱하고 my_transformer를 통해 해당 쿼리를 처리해 주었습니다. 이때 exception이 발생하면 몇 번째 쿼리의 어느 부분에서 에러가 발생하였는지 프린트하고 이번 턴의 처리를 종료하도록 하였습니다.

## 프로젝트를 하면서 느낀 점 및 기타사항

스펙의 예시에서는 Transformer 클래스를 통해 입력받은 구문을 처리해야 한다고 되어 있었는데, 현재까지는 입력받은 쿼리를 파싱하고 해당하는 sql의 종류를 출력하도록 구현하였기 때문에 transformer 클래스의 transform() 함수를 사용하게 되면 필요한 내용을 출력하기만 하고 어떠한 처리도 할 수 없었습니다. 추후 과제 1-2, 1-3에서는 사용하지 않은 transformer 클래스의 기능들을 사용하게 되는 것인지, 아니라면 왜 Visitor 클래스 대신 Transformer 클래스가 예시에 사용된 것인지 궁금하였습니다.

