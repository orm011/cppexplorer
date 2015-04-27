struct Baz {
  int x;
  void foo(){
    x++;
  }
};

class Foo {
    class Bar {
      void bara() {
    	a++;
	b++;
      }

      int a;
      int b;
    };


  void methoda() {
    x++;
    y++;
    methodb();

    class Bar {
      void bara() {
    	a++;
	b++;
      }

      int a;
      int b;
    };
  }


  void methodb() {
    y++;
    z++;
    z++;

    if (x > y) {
      x = y;
    }
  }

  void methodc() {
    y = y + z;
  }

  void  methodd() {
    x++;
    y++;
    z++;
  }
private:
  int x;
  int y;
  int z;
};
