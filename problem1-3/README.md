# SQL parser의 확장을 통한 DBMS 구현(DDL, DML)

## 핵심 모듈, 알고리즘 설명

프로젝트 1-1에서 구현한 parser, 프로젝트 1-2에서 구현한 일부 DDL, DML에 이어 Insert, Delete, Select를 추가적으로 구현하였습니다. 프로젝트 1-2에서는 insert되는 모든 record 가 전부 valid한 instance라고 가정하였으나, 이번 프로젝트에서는 pk, fk constraint를 위 반하는 입력이 들어오지 않는다고만 가정하였습니다. 따라서 insert를 위해서는 다양한 조건들이 위배되지 않는지 우선적으로 검사합니다. Grammar.lark를 통해 파싱된 토큰의 type 값이 db에 저장된 해당 column의 type과 다른 경우, column_clause나 value_clause 의 attr 수가 해당 table의 실제 attr 수와 다른 경우, not null constraint가 있는 attr에 null 값을 삽입한 경우, column_clause의 column name이 실제 attr 이름과 다른 경우 등 에는 적절한 에러 메시지를 출력합니다. Column_clause로 입력된 column 순서가 db에 저장된 순서와 다른 경우(수는 같음)에는 에러를 발생시키지 않고 해당 순서로 db에 입 력한 value를 저장하게 됩니다.

Select의 경우 from→where→select의 순서로 query를 처리합니다.From 단계에서는 주 어진 table을 cartesian product한 새로운 temporary from table을 생성합니다. 이때 콜롬 이름이 겹칠 수 있기 때문에 모든 콜롬에 대해 “테이블명.콜롬명”(겹치는 경우) 혹은 “콜 롬명”(겹치지 않는 경우)을 저장하는 list 하나, 같은 순서로 콜롬명만 저장하는 list 하나, 같은 순서로 테이블명만 저장하는 list 하나를 각각 생성합니다(구체적인 이유는 2번에 설 명). Where 단계에서는 다시 두 가지 step을 거칩니다. 첫째, test_where() 함수를 통해 파 싱된 where_clause 자체에 문법적 오류가 있는지 찾아냅니다. 즉 type이 달라 비교할 수 없는 값들을 비교하려고 했다거나, 존재하지 않는 콜롬을 비교하려고 했다든가, 콜롬명이 모호한 경우 등에는 해당하는 에러 메시지를 출력하고 작업을 중단하게 됩니다. 둘째, where_clause에 문법적인 오류가 없다면 test() 함수를 통해 recursive하게 각 Boolean test를 처리하게 됩니다. From 단계를 통해 cartesian product된 테이블에 대한 스키마를 얻고, where 단계를 통해 그 테이블에 들어갈 record들을 얻었다면 마지막으로 select 단 계를 통해 명시된 콜롬의 record들만 project하게 됩니다. Delete의 경우 where 단계는 select와 동일하며, where 단계에서 얻어진 record들의 index들을 저장해 두었다가 해당 index의 record만 제거한 새로운 table을 db에 삽입하도록 구현하였습니다.

## 추가 가정/구현 사항
 
* insert 구문에서 명시적으로 column을 적어주는 경우 그 set이 기존 set과 다르다면 에러를 발생시킨다. 즉 개수가 다를 때 뿐만 아니라 중복된 column이 있을 때도 에러를 내는 것.

* Select 절이나 where 절에서 이미 unique한 column임에도 불구하고 table name을 suffix로 적어준 경우 에러를 발생시키지 않고 제대로 작동하도록 한다. 이를 위해서 콜롬명과 테이블명을 저장하는 세 개의 list를 생성해 주었던 것이다. 또 이때 suffix 의 table이 from에서 명시해주지 않은 테이블인 경우도 칼럼 이름을 해석하는 데에 문제가 있는 것으로 보아 같은 에러메시지를 발생시킨다.

* From 절에서 명시한 테이블 중에 빈 테이블이 있다면 총 cartesian product된 테이블 또한 빈 테이블이 된다.

* Grammar.lark 파일을 수정하여 NULL을 구분할 수 있도록 하였음. 일반적인 str 입력 값은 quote으로 시작하기에 null을 별도 terminal로 지정해 놓으면 구분 가능하다.

